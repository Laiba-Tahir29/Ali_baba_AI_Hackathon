# Interface Contract

Person B: extract_profile(pdf_path) 
→ list of per-report profiles:
[{date, doctor, age, bp, cholesterol, glucose, bmi, smoking, history}, ...]

Person B: consolidate_profiles(profiles_list)
→ final_profile:
{age, bp, cholesterol, glucose, bmi, smoking, history, consistent_high_factors: [...]}

Person A: predict_risk(final_profile)
→ {risk_score, risk_level, top_factors}

Person B: generate_explanation(risk_data, consistent_high_factors, evidence)
→ string