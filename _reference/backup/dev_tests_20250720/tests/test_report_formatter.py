"""
Unit tests for ReportFormatter service
Tests positive framing, language transformations, and edge cases
"""

import pytest
from datetime import datetime
from app.services.report_formatter import ReportFormatter


class TestReportFormatter:
    """Test suite for ReportFormatter"""
    
    @pytest.fixture
    def formatter(self):
        """Create a ReportFormatter instance"""
        return ReportFormatter()
    
    @pytest.fixture
    def minimal_coverage_data(self):
        """Test data for minimal coverage scenario"""
        return {
            "report_info": {
                "report_id": 156,
                "report_name": "FR Y-14Q Capital Assessments",
                "report_type": "Regulatory",
                "frequency": "Quarterly"
            },
            "cycle_info": {
                "cycle_id": 21,
                "cycle_name": "Q3 2024 Testing Cycle",
                "period": "Q3 2024"
            },
            "executive_summary": {
                "key_metrics": {
                    "total_attributes": 114,
                    "attributes_tested": 1,
                    "coverage_percentage": 0.88,
                    "pass_rate": 100,
                    "total_issues": 0,
                    "high_severity_issues": 0
                }
            }
        }
    
    def test_format_report_with_minimal_coverage(self, formatter, minimal_coverage_data):
        """Test formatting with minimal coverage emphasizes positive framing"""
        result = formatter.format_report(minimal_coverage_data)
        
        # Check executive summary uses positive language
        assert "strategically" in result['executive_summary']['overview'].lower()
        assert "targeted" in result['executive_summary']['overview'].lower()
        assert "critical" in result['executive_summary']['overview'].lower()
        
        # Check key achievements
        achievements = result['executive_summary']['key_achievements']
        assert len(achievements) >= 3
        assert any("100% pass rate" in achievement for achievement in achievements)
        assert any("risk methodology" in achievement for achievement in achievements)
        
        # Check coverage classification
        assert result['testing_coverage']['coverage_classification'] == "Targeted Risk-Based Coverage"
        assert "superior assurance" in result['testing_coverage']['coverage_narrative']
    
    def test_format_report_with_moderate_coverage(self, formatter):
        """Test formatting with moderate coverage (25%)"""
        data = {
            "report_info": {"report_name": "Test Report", "report_id": 1},
            "cycle_info": {"cycle_name": "Test Cycle", "period": "Q1 2024"},
            "executive_summary": {
                "key_metrics": {
                    "total_attributes": 100,
                    "attributes_tested": 25,
                    "coverage_percentage": 25,
                    "pass_rate": 90,
                    "total_issues": 5,
                    "high_severity_issues": 1
                }
            }
        }
        
        result = formatter.format_report(data)
        
        # Should use appropriate language for 25% coverage
        # 25% is the threshold where it switches to "Comprehensive Risk-Based Methodology"
        assert "comprehensive" in result['strategic_approach']['approach_type'].lower()
        assert result['testing_coverage']['coverage_classification'] == "Balanced Risk Coverage"
    
    def test_format_report_with_high_coverage(self, formatter):
        """Test formatting with high coverage (75%)"""
        data = {
            "report_info": {"report_name": "Test Report", "report_id": 1},
            "cycle_info": {"cycle_name": "Test Cycle", "period": "Q1 2024"},
            "executive_summary": {
                "key_metrics": {
                    "total_attributes": 100,
                    "attributes_tested": 75,
                    "coverage_percentage": 75,
                    "pass_rate": 95,
                    "total_issues": 3,
                    "high_severity_issues": 0
                }
            }
        }
        
        result = formatter.format_report(data)
        
        # Should emphasize comprehensive coverage
        assert "comprehensive" in result['strategic_approach']['approach_type'].lower()
        assert result['testing_coverage']['coverage_classification'] == "Comprehensive Coverage"
    
    def test_format_report_with_missing_data(self, formatter):
        """Test formatting handles missing data gracefully"""
        # Test with empty dict
        result = formatter.format_report({})
        
        # Should not throw error and have default values
        assert result['metadata']['report_title'] == "Test Report Testing Report"
        assert result['executive_summary']['overview'] is not None
        assert result['testing_coverage']['coverage_percentage'] == 0
    
    def test_format_report_with_partial_data(self, formatter):
        """Test formatting handles partial data"""
        data = {
            "report_info": {"report_name": "Partial Report"}
            # Missing cycle_info and executive_summary
        }
        
        result = formatter.format_report(data)
        
        # Should use provided data where available and defaults elsewhere
        assert "Partial Report" in result['metadata']['report_title']
        assert result['metadata']['period'] == "Unknown Period"
        assert result['executive_summary']['metrics_summary']['coverage'] == "0% strategically concentrated"
    
    def test_positive_language_transformations(self, formatter):
        """Test that negative phrases are transformed positively"""
        # Test with very low coverage
        data = {
            "executive_summary": {
                "key_metrics": {
                    "total_attributes": 1000,
                    "attributes_tested": 5,
                    "coverage_percentage": 0.5,
                    "pass_rate": 100
                }
            }
        }
        
        result = formatter.format_report(data)
        
        # Should never use negative terms
        narrative = result['testing_coverage']['coverage_narrative'].lower()
        assert "only" not in narrative
        assert "just" not in narrative
        assert "limited" not in narrative
        assert "insufficient" not in narrative
        
        # Should use positive terms
        assert "strategic" in narrative or "targeted" in narrative or "focused" in narrative
    
    def test_regulatory_body_extraction(self, formatter):
        """Test regulatory body extraction from report names"""
        test_cases = [
            ("FR Y-14Q", "Federal Reserve"),
            ("FR Y-9C", "Federal Reserve"),
            ("FFIEC 031", "FFIEC"),
            ("Call Report Schedule RC", "FDIC/OCC"),
            ("Custom Report", "Regulatory Authority")
        ]
        
        for report_name, expected_body in test_cases:
            data = {"report_info": {"report_name": report_name}}
            result = formatter.format_report(data)
            assert result['metadata']['regulatory_body'] == expected_body
    
    def test_markdown_generation(self, formatter, minimal_coverage_data):
        """Test markdown generation includes all sections"""
        result = formatter.format_report(minimal_coverage_data)
        
        markdown = result['markdown']
        assert "# FR Y-14Q Capital Assessments Testing Report" in markdown
        assert "## Executive Summary" in markdown
        assert "## Strategic Testing Approach" in markdown
        assert "### Key Achievements" in markdown
        assert "✓" in markdown  # Check for checkmarks
    
    def test_html_generation(self, formatter, minimal_coverage_data):
        """Test HTML generation with proper structure"""
        result = formatter.format_report(minimal_coverage_data)
        
        html = result['html']
        assert "<!DOCTYPE html>" in html
        assert "<title>FR Y-14Q Capital Assessments Testing Report</title>" in html
        assert "<style>" in html  # Check for styling
        assert "font-family:" in html  # Check CSS is included
    
    def test_perfect_pass_rate_messaging(self, formatter):
        """Test messaging for 100% pass rate"""
        data = {
            "executive_summary": {
                "key_metrics": {
                    "total_attributes": 50,
                    "attributes_tested": 25,
                    "coverage_percentage": 50,
                    "pass_rate": 100,
                    "total_issues": 0
                }
            }
        }
        
        result = formatter.format_report(data)
        
        # Should emphasize strong control environment
        achievements = result['executive_summary']['key_achievements']
        assert any("100% pass rate" in achievement for achievement in achievements)
        assert any("robust control environment" in achievement for achievement in achievements)
    
    def test_issues_found_positive_framing(self, formatter):
        """Test that found issues are framed positively"""
        data = {
            "executive_summary": {
                "key_metrics": {
                    "total_attributes": 100,
                    "attributes_tested": 50,
                    "coverage_percentage": 50,
                    "pass_rate": 80,
                    "total_issues": 10,
                    "high_severity_issues": 2
                }
            }
        }
        
        result = formatter.format_report(data)
        
        # Should frame issues as opportunities
        results_desc = result['testing_results']['quality_achievements']['description']
        assert "opportunities" in results_desc.lower() or "insights" in results_desc.lower()
        assert "failed" not in results_desc.lower()
        assert "errors" not in results_desc.lower()
    
    def test_value_delivery_section(self, formatter):
        """Test value delivery section generation"""
        data = {
            "executive_summary": {
                "key_metrics": {
                    "total_issues": 5,
                    "high_severity_issues": 2
                }
            }
        }
        
        result = formatter.format_report(data)
        
        value_section = result['value_delivery']
        assert len(value_section['quantifiable_benefits']) > 0
        assert len(value_section['qualitative_benefits']) > 0
        assert "Prevented 2 potential regulatory findings" in value_section['quantifiable_benefits']
    
    def test_recommendations_based_on_coverage(self, formatter):
        """Test recommendations adapt to coverage level"""
        # Low coverage
        low_coverage_data = {
            "executive_summary": {
                "key_metrics": {"coverage_percentage": 10}
            }
        }
        low_result = formatter.format_report(low_coverage_data)
        
        # High coverage
        high_coverage_data = {
            "executive_summary": {
                "key_metrics": {"coverage_percentage": 80}
            }
        }
        high_result = formatter.format_report(high_coverage_data)
        
        # Recommendations should differ
        low_recs = low_result['recommendations']['building_on_success']
        high_recs = high_result['recommendations']['building_on_success']
        
        assert "Phase 2" in str(low_recs)
        assert "comprehensive coverage" in str(high_recs).lower()
    
    def test_attestation_varies_by_coverage(self, formatter):
        """Test attestation text varies based on coverage"""
        # Low coverage
        low_data = {
            "executive_summary": {
                "key_metrics": {"coverage_percentage": 5}
            }
        }
        low_result = formatter.format_report(low_data)
        
        # High coverage  
        high_data = {
            "executive_summary": {
                "key_metrics": {"coverage_percentage": 75}
            }
        }
        high_result = formatter.format_report(high_data)
        
        assert low_result['attestation']['type'] == "Strategic Testing Attestation"
        assert high_result['attestation']['type'] == "Comprehensive Testing Attestation"
        assert "risk-based" in low_result['attestation']['text'].lower()
        assert "comprehensive" in high_result['attestation']['text'].lower()


class TestReportFormatterHelpers:
    """Test helper methods"""
    
    def test_deep_merge(self):
        """Test deep merge functionality"""
        formatter = ReportFormatter()
        
        default = {
            "a": 1,
            "b": {"c": 2, "d": 3},
            "e": [1, 2, 3]
        }
        
        override = {
            "a": 10,
            "b": {"c": 20, "x": 30},
            "f": 40
        }
        
        result = formatter._deep_merge(default, override)
        
        assert result["a"] == 10
        assert result["b"]["c"] == 20
        assert result["b"]["d"] == 3  # Preserved from default
        assert result["b"]["x"] == 30  # Added from override
        assert result["e"] == [1, 2, 3]  # Preserved from default
        assert result["f"] == 40  # Added from override
    
    def test_coverage_classification(self):
        """Test coverage classification logic"""
        formatter = ReportFormatter()
        
        test_cases = [
            (0, "Targeted Risk-Based Coverage"),
            (4.9, "Targeted Risk-Based Coverage"),
            (5, "Focused Risk-Based Coverage"),
            (24.9, "Focused Risk-Based Coverage"),
            (25, "Balanced Risk Coverage"),
            (49.9, "Balanced Risk Coverage"),
            (50, "Broad Risk Coverage"),
            (74.9, "Broad Risk Coverage"),
            (75, "Comprehensive Coverage"),
            (100, "Comprehensive Coverage")
        ]
        
        for coverage, expected_classification in test_cases:
            assert formatter._classify_coverage(coverage) == expected_classification


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])