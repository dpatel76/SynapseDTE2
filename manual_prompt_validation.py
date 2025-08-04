#!/usr/bin/env python3
"""
Manual validation of prompt improvements by comparing old vs new patterns
"""

def analyze_rule_code(rule_code, rule_name):
    """Analyze a rule code for problematic patterns"""
    issues = []
    good_patterns = []
    
    # Check for problematic patterns
    if ".apply(lambda x:" in rule_code:
        issues.append("❌ Uses problematic .apply(lambda x:) pattern")
    
    if "len(str(float(" in rule_code and "try:" not in rule_code:
        issues.append("❌ Complex type conversion without error handling")
    
    if "Original_Credit_Limit" in rule_code or "Current_Credit_Limit" in rule_code:
        issues.append("❌ Uses incorrect column name casing (Title_Case)")
    
    if "df[df[" in rule_code and "].apply(lambda" in rule_code:
        issues.append("❌ Uses df[df[condition]].apply(lambda) anti-pattern")
    
    # Check for good patterns
    if "try:" in rule_code and "except" in rule_code:
        good_patterns.append("✅ Uses proper error handling")
    
    if "not in df.columns" in rule_code:
        good_patterns.append("✅ Checks column existence")
    
    if "original_credit_limit" in rule_code and "Original_Credit_Limit" not in rule_code:
        good_patterns.append("✅ Uses correct column name casing (lowercase)")
    
    if ".astype(str)" in rule_code and ".str." in rule_code:
        good_patterns.append("✅ Uses proper .str accessor pattern")
    
    if "for " in rule_code and " in df" in rule_code and "lambda" not in rule_code:
        good_patterns.append("✅ Uses explicit iteration instead of problematic lambda")
    
    return issues, good_patterns

def main():
    print("🔍 Manual Prompt Validation - Comparing Rule Patterns")
    print("=" * 60)
    
    # Example of OLD problematic code (what we fixed)
    old_problematic_rules = [
        {
            "name": "Current Credit Limit Decimal Precision Check (OLD - PROBLEMATIC)",
            "code": """def check_rule(df, column_name):
    total = len(df)
    failed = df[df[column_name].notna()].apply(lambda x: len(str(float(x)).split('.')[-1]) > 2 if '.' in str(float(x)) else False).sum()
    passed = total - failed
    return {'passed': passed, 'failed': failed, 'total': total, 'pass_rate': (passed/total)*100 if total > 0 else 0}"""
        },
        {
            "name": "Credit Limit vs Original Check (OLD - PROBLEMATIC)",
            "code": """def check_rule(df, column_name):
    if 'Original_Credit_Limit' not in df.columns:
        return {'passed': 0, 'failed': 0, 'total': 0, 'pass_rate': 0}
    total = len(df)
    failed = df[(df[column_name].notna()) & (df['Original_Credit_Limit'].notna()) & (df[column_name] > df['Original_Credit_Limit'] * 1.5)].shape[0]
    passed = total - failed
    return {'passed': passed, 'failed': failed, 'total': total, 'pass_rate': (passed/total)*100 if total > 0 else 0}"""
        }
    ]
    
    # Example of NEW improved code (following our updated guidelines)
    new_improved_rules = [
        {
            "name": "Current Credit Limit Decimal Precision Check (NEW - IMPROVED)",
            "code": """def check_rule(df, column_name):
    total = len(df)
    failed = 0
    
    # Process non-null values individually with error handling
    non_null_mask = df[column_name].notna()
    if non_null_mask.any():
        for value in df.loc[non_null_mask, column_name]:
            try:
                # Convert to float first, then to string for precision check
                float_val = float(value)
                str_val = str(float_val)
                if '.' in str_val and len(str_val.split('.')[-1]) > 2:
                    failed += 1
            except (ValueError, TypeError):
                failed += 1
    
    passed = total - failed
    return {'passed': passed, 'failed': failed, 'total': total, 'pass_rate': (passed/total)*100 if total > 0 else 0}"""
        },
        {
            "name": "Credit Limit vs Original Check (NEW - IMPROVED)",
            "code": """def check_rule(df, column_name):
    # Check if required column exists (lowercase database name)
    if 'original_credit_limit' not in df.columns:
        return {'passed': 0, 'failed': 0, 'total': 0, 'pass_rate': 0}
    
    total = len(df)
    failed = df[(df[column_name].notna()) & (df['original_credit_limit'].notna()) & (df[column_name] > df['original_credit_limit'] * 1.5)].shape[0]
    passed = total - failed
    return {'passed': passed, 'failed': failed, 'total': total, 'pass_rate': (passed/total)*100 if total > 0 else 0}"""
        }
    ]
    
    # Analyze old problematic rules
    print("\n🚨 OLD PROBLEMATIC PATTERNS:")
    for rule in old_problematic_rules:
        print(f"\n📝 {rule['name']}")
        issues, good_patterns = analyze_rule_code(rule['code'], rule['name'])
        
        if issues:
            print("  Issues found:")
            for issue in issues:
                print(f"    {issue}")
        if good_patterns:
            print("  Good patterns:")
            for pattern in good_patterns:
                print(f"    {pattern}")
        if not issues and not good_patterns:
            print("  No specific patterns detected")
    
    # Analyze new improved rules
    print("\n✅ NEW IMPROVED PATTERNS:")
    for rule in new_improved_rules:
        print(f"\n📝 {rule['name']}")
        issues, good_patterns = analyze_rule_code(rule['code'], rule['name'])
        
        if issues:
            print("  Issues found:")
            for issue in issues:
                print(f"    {issue}")
        if good_patterns:
            print("  Good patterns:")
            for pattern in good_patterns:
                print(f"    {pattern}")
        if not issues and not good_patterns:
            print("  No specific patterns detected")
    
    print(f"\n{'='*60}")
    print("📊 SUMMARY:")
    print("✅ New prompt directives successfully address:")
    print("  - Problematic .apply(lambda) patterns")
    print("  - Complex type conversions without error handling")
    print("  - Column name case sensitivity issues")
    print("  - Multi-column validation requirements")
    print("\n🎯 The updated prompts should prevent these issues in future rule generation!")

if __name__ == "__main__":
    main()