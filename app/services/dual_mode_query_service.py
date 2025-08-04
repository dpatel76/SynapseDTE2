"""
Dual-mode query service for Request Info and Testing phases
Supports both document-based LLM analysis and direct database queries
"""
from typing import Dict, List, Optional, Union, Any, Tuple
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import json
import pandas as pd
from dataclasses import dataclass

from app.models.data_source import DataSource, DataQuery, SecurityClassification
from app.models.request_info import RequestInfoPhase
from app.models.test_execution import TestExecution
from app.core.database import AsyncSessionLocal
from app.core.security.data_masking import DataMaskingService, SecureQueryBuilder
from app.services.llm_service import HybridLLMService
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result from query execution"""
    success: bool
    data: Optional[Union[pd.DataFrame, Dict[str, Any]]]
    error: Optional[str]
    row_count: Optional[int]
    execution_time_ms: Optional[int]
    masked_fields: Optional[List[str]]


@dataclass
class TestResult:
    """Result from test execution"""
    test_id: str
    test_name: str
    passed: bool
    expected_value: Any
    actual_value: Any
    confidence_score: Optional[float]
    evidence: Optional[Dict[str, Any]]
    error_message: Optional[str]


class DualModeQueryService:
    """Service for dual-mode querying - LLM and direct database"""
    
    def __init__(
        self, 
        llm_service: Optional[HybridLLMService] = None,
        masking_service: Optional[DataMaskingService] = None
    ):
        self.llm_service = llm_service or HybridLLMService()
        self.masking_service = masking_service or DataMaskingService()
        self.query_executor = DatabaseQueryExecutor(masking_service)
        self.document_analyzer = DocumentAnalyzer(llm_service)
    
    async def execute_request_info_query(
        self,
        request_info_id: int,
        query_mode: str,  # 'document' or 'database'
        query_params: Dict[str, Any],
        user: User,
        session: AsyncSession
    ) -> QueryResult:
        """Execute query for request info phase"""
        try:
            # Get request info details
            request_info = await session.get(RequestInfoPhase, request_info_id)
            if not request_info:
                return QueryResult(
                    success=False,
                    data=None,
                    error="Request info not found",
                    row_count=None,
                    execution_time_ms=None,
                    masked_fields=None
                )
            
            if query_mode == 'document':
                # Use LLM to analyze uploaded documents
                return await self.document_analyzer.analyze_documents(
                    request_info,
                    query_params,
                    session
                )
            else:
                # Execute direct database query
                return await self.query_executor.execute_query(
                    request_info.report_id,
                    query_params,
                    user,
                    session
                )
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return QueryResult(
                success=False,
                data=None,
                error=str(e),
                row_count=None,
                execution_time_ms=None,
                masked_fields=None
            )
    
    async def execute_test(
        self,
        test_execution_id: int,
        test_mode: str,  # 'llm' or 'query'
        test_params: Dict[str, Any],
        user: User,
        session: AsyncSession
    ) -> TestResult:
        """Execute test in specified mode"""
        try:
            # Get test execution details
            test_execution = await session.get(TestExecution, test_execution_id)
            if not test_execution:
                return TestResult(
                    test_id=str(test_execution_id),
                    test_name="Unknown",
                    passed=False,
                    expected_value=None,
                    actual_value=None,
                    confidence_score=None,
                    evidence=None,
                    error_message="Test execution not found"
                )
            
            if test_mode == 'llm':
                # Use LLM to test against documents
                return await self._execute_llm_test(
                    test_execution,
                    test_params,
                    session
                )
            else:
                # Execute direct query-based test
                return await self._execute_query_test(
                    test_execution,
                    test_params,
                    user,
                    session
                )
            
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            return TestResult(
                test_id=str(test_execution_id),
                test_name=test_params.get('test_name', 'Unknown'),
                passed=False,
                expected_value=test_params.get('expected_value'),
                actual_value=None,
                confidence_score=None,
                evidence=None,
                error_message=str(e)
            )
    
    async def _execute_llm_test(
        self,
        test_execution: TestExecution,
        test_params: Dict[str, Any],
        session: AsyncSession
    ) -> TestResult:
        """Execute test using LLM analysis"""
        # Get related documents
        documents = await self._get_test_documents(test_execution, session)
        
        # Build test prompt
        prompt = self._build_test_prompt(test_execution, test_params, documents)
        
        # Execute LLM analysis
        llm_result = await self.llm_service.analyze_for_testing(prompt)
        
        # Parse results
        return TestResult(
            test_id=str(test_execution.execution_id),
            test_name=test_params.get('test_name', test_execution.attribute.attribute_name),
            passed=llm_result.get('passed', False),
            expected_value=test_params.get('expected_value'),
            actual_value=llm_result.get('actual_value'),
            confidence_score=llm_result.get('confidence', 0.0),
            evidence=llm_result.get('evidence', {}),
            error_message=None
        )
    
    async def _execute_query_test(
        self,
        test_execution: TestExecution,
        test_params: Dict[str, Any],
        user: User,
        session: AsyncSession
    ) -> TestResult:
        """Execute test using database query"""
        # Build test query
        query = await self._build_test_query(test_execution, test_params, session)
        
        # Execute query
        query_result = await self.query_executor.execute_query(
            test_execution.report_id,
            {'query': query, 'parameters': test_params.get('query_params', {})},
            user,
            session
        )
        
        if not query_result.success:
            return TestResult(
                test_id=str(test_execution.execution_id),
                test_name=test_params.get('test_name', test_execution.attribute.attribute_name),
                passed=False,
                expected_value=test_params.get('expected_value'),
                actual_value=None,
                confidence_score=1.0,  # Query results are definitive
                evidence={'query_error': query_result.error},
                error_message=query_result.error
            )
        
        # Compare results
        actual_value = self._extract_test_value(query_result.data)
        expected_value = test_params.get('expected_value')
        
        passed = self._compare_values(actual_value, expected_value, test_params.get('comparison_type', 'equals'))
        
        return TestResult(
            test_id=str(test_execution.execution_id),
            test_name=test_params.get('test_name', test_execution.attribute.attribute_name),
            passed=passed,
            expected_value=expected_value,
            actual_value=actual_value,
            confidence_score=1.0,  # Query results are definitive
            evidence={
                'query': query,
                'row_count': query_result.row_count,
                'execution_time_ms': query_result.execution_time_ms
            },
            error_message=None
        )
    
    async def _get_test_documents(
        self,
        test_execution: TestExecution,
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get documents related to test"""
        # Placeholder - would fetch actual documents
        return []
    
    def _build_test_prompt(
        self,
        test_execution: TestExecution,
        test_params: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for LLM testing"""
        return f"""
        Test the following attribute from the documents provided:
        
        Attribute: {test_execution.attribute.attribute_name}
        Description: {test_execution.attribute.description}
        Expected Value: {test_params.get('expected_value')}
        Test Type: {test_params.get('test_type', 'exact_match')}
        
        Documents:
        {json.dumps(documents, indent=2)}
        
        Please analyze the documents and determine:
        1. The actual value of the attribute
        2. Whether it matches the expected value
        3. Confidence level (0-1)
        4. Supporting evidence from the documents
        """
    
    async def _build_test_query(
        self,
        test_execution: TestExecution,
        test_params: Dict[str, Any],
        session: AsyncSession
    ) -> str:
        """Build SQL query for test"""
        # Get attribute mapping
        mapping = await session.execute(
            select(AttributeMapping).filter(
                AttributeMapping.attribute_id == test_execution.attribute_id
            ).limit(1)
        )
        mapping = mapping.scalar_one_or_none()
        
        if not mapping:
            raise ValueError("No mapping found for attribute")
        
        # Build query based on test type
        test_type = test_params.get('test_type', 'aggregate')
        
        if test_type == 'aggregate':
            return f"""
                SELECT 
                    COUNT(*) as count,
                    SUM({mapping.column_name}) as sum,
                    AVG({mapping.column_name}) as average,
                    MIN({mapping.column_name}) as min,
                    MAX({mapping.column_name}) as max
                FROM {mapping.table_name}
                WHERE {test_params.get('where_clause', '1=1')}
            """
        elif test_type == 'sample':
            return f"""
                SELECT {mapping.column_name}
                FROM {mapping.table_name}
                WHERE {test_params.get('where_clause', '1=1')}
                LIMIT {test_params.get('sample_size', 100)}
            """
        else:
            return test_params.get('custom_query', '')
    
    def _extract_test_value(self, data: Union[pd.DataFrame, Dict[str, Any]]) -> Any:
        """Extract test value from query result"""
        if isinstance(data, pd.DataFrame):
            if len(data) == 1 and len(data.columns) == 1:
                return data.iloc[0, 0]
            elif 'sum' in data.columns:
                return data['sum'].iloc[0]
            elif 'count' in data.columns:
                return data['count'].iloc[0]
        elif isinstance(data, dict):
            return data.get('value', data)
        
        return data
    
    def _compare_values(
        self,
        actual: Any,
        expected: Any,
        comparison_type: str
    ) -> bool:
        """Compare actual and expected values"""
        try:
            if comparison_type == 'equals':
                return actual == expected
            elif comparison_type == 'greater_than':
                return float(actual) > float(expected)
            elif comparison_type == 'less_than':
                return float(actual) < float(expected)
            elif comparison_type == 'between':
                min_val, max_val = expected
                return float(min_val) <= float(actual) <= float(max_val)
            elif comparison_type == 'contains':
                return str(expected) in str(actual)
            elif comparison_type == 'regex':
                import re
                return bool(re.match(expected, str(actual)))
            else:
                return actual == expected
        except Exception as e:
            logger.error(f"Value comparison failed: {str(e)}")
            return False


class DatabaseQueryExecutor:
    """Executes database queries with security controls"""
    
    def __init__(self, masking_service: DataMaskingService):
        self.masking_service = masking_service
        self.query_builder = SecureQueryBuilder(
            FieldLevelSecurity(masking_service)
        )
    
    async def execute_query(
        self,
        report_id: int,
        query_params: Dict[str, Any],
        user: User,
        session: AsyncSession
    ) -> QueryResult:
        """Execute database query with security controls"""
        start_time = datetime.utcnow()
        masked_fields = []
        
        try:
            # Get data source
            data_source = await self._get_data_source(report_id, session)
            if not data_source:
                return QueryResult(
                    success=False,
                    data=None,
                    error="No data source configured for report",
                    row_count=None,
                    execution_time_ms=None,
                    masked_fields=None
                )
            
            # Build secure query
            if query_params.get('auto_build', True):
                query, masked_fields = await self._build_secure_query(
                    report_id,
                    query_params,
                    user,
                    session
                )
            else:
                query = query_params.get('query', '')
            
            # Execute query
            result = await self._execute_raw_query(
                data_source,
                query,
                query_params.get('parameters', {})
            )
            
            # Apply post-query masking if needed
            if masked_fields and isinstance(result, pd.DataFrame):
                for field in masked_fields:
                    if field in result.columns:
                        result[field] = '***MASKED***'
            
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return QueryResult(
                success=True,
                data=result,
                error=None,
                row_count=len(result) if isinstance(result, pd.DataFrame) else 1,
                execution_time_ms=execution_time,
                masked_fields=masked_fields
            )
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return QueryResult(
                success=False,
                data=None,
                error=str(e),
                row_count=None,
                execution_time_ms=None,
                masked_fields=masked_fields
            )
    
    async def _get_data_source(
        self,
        report_id: int,
        session: AsyncSession
    ) -> Optional[DataSource]:
        """Get active data source for report"""
        result = await session.execute(
            select(DataSource).filter(
                DataSource.report_id == report_id,
                DataSource.is_active == True
            ).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def _build_secure_query(
        self,
        report_id: int,
        query_params: Dict[str, Any],
        user: User,
        session: AsyncSession
    ) -> Tuple[str, List[str]]:
        """Build secure query with masking"""
        # Get table and columns from params
        table = query_params.get('table')
        columns = query_params.get('columns', ['*'])
        where_clause = query_params.get('where_clause')
        
        # Get field security policies
        masked_fields = []
        secure_columns = []
        
        for column in columns:
            if column == '*':
                # Would expand to all columns with security checks
                secure_columns.append(column)
            else:
                # Check if column needs masking
                field_security = FieldLevelSecurity(self.masking_service)
                if field_security.should_mask(table, column, user, 'view'):
                    secure_columns.append(f"'***MASKED***' AS {column}")
                    masked_fields.append(column)
                else:
                    secure_columns.append(column)
        
        # Build query
        query = f"SELECT {', '.join(secure_columns)} FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        return query, masked_fields
    
    async def _execute_raw_query(
        self,
        data_source: DataSource,
        query: str,
        parameters: Dict[str, Any]
    ) -> pd.DataFrame:
        """Execute raw query against data source"""
        # Get connection details
        config = data_source.decrypt_config()
        
        # This would use appropriate database driver
        # Placeholder implementation
        import pandas as pd
        
        # Simulate query execution
        if "COUNT" in query.upper():
            return pd.DataFrame({'count': [100]})
        elif "SUM" in query.upper():
            return pd.DataFrame({
                'count': [100],
                'sum': [10000],
                'average': [100],
                'min': [10],
                'max': [500]
            })
        else:
            # Return sample data
            return pd.DataFrame({
                'id': range(10),
                'value': [i * 100 for i in range(10)]
            })


class DocumentAnalyzer:
    """Analyzes documents using LLM"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def analyze_documents(
        self,
        request_info: RequestInfoPhase,
        query_params: Dict[str, Any],
        session: AsyncSession
    ) -> QueryResult:
        """Analyze uploaded documents"""
        try:
            # Get documents
            documents = await self._get_documents(request_info, session)
            
            # Build analysis prompt
            prompt = self._build_analysis_prompt(query_params, documents)
            
            # Execute LLM analysis
            start_time = datetime.utcnow()
            result = await self.llm_service.analyze_documents(prompt)
            end_time = datetime.utcnow()
            
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return QueryResult(
                success=True,
                data=result,
                error=None,
                row_count=len(documents),
                execution_time_ms=execution_time,
                masked_fields=[]
            )
            
        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}")
            return QueryResult(
                success=False,
                data=None,
                error=str(e),
                row_count=None,
                execution_time_ms=None,
                masked_fields=None
            )
    
    async def _get_documents(
        self,
        request_info: RequestInfoPhase,
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get documents for analysis"""
        # Placeholder - would fetch actual documents
        return [
            {
                'name': 'report_q4_2023.pdf',
                'content': 'CycleReportSampleSelectionSamples document content...',
                'metadata': {'pages': 10, 'size': '2MB'}
            }
        ]
    
    def _build_analysis_prompt(
        self,
        query_params: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for document analysis"""
        questions = query_params.get('questions', [])
        attributes = query_params.get('attributes', [])
        
        return f"""
        Analyze the following documents to answer questions and extract attribute values:
        
        Questions:
        {json.dumps(questions, indent=2)}
        
        Attributes to Extract:
        {json.dumps(attributes, indent=2)}
        
        Documents:
        {json.dumps(documents, indent=2)}
        
        Please provide:
        1. Answers to each question with supporting evidence
        2. Values for each requested attribute
        3. Confidence level for each answer/value
        4. Page/section references where information was found
        """