import pandas as pd
from datetime import datetime
import json
import re
import openai
import os
from typing import Dict, List
import time
from pydantic import BaseModel, Field

class CompanyAnalysis(BaseModel):
    """Pydantic model for GPT company analysis response"""
    is_saas: bool
    growth_potential: int
    risk_level: int
    key_strengths: List[str]
    concerns: List[str]
    target_market: str
    competitive_advantage: str

class CompanyClassifier:
    def __init__(self, data_path: str, openai_key: str):
        """Initialize classifier with data and OpenAI key"""
        self.df = pd.read_csv(data_path)
        self.current_year = datetime.now().year
        openai.api_key = openai_key

    def get_gpt_analysis(self, company_name: str, description: str, industry: str) -> CompanyAnalysis:
        """
        Use GPT to analyze company description and provide insights
        Returns validated CompanyAnalysis object
        """
        prompt = f"""
        Analyze this company and provide structured insights:
        Company: {company_name}
        Industry: {industry}
        Description: {description}
        """

        try:    
            response = openai.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[{"role": "system", "content": f"You are a venture capital analyst expert at analyzing technology companies. Provide analysis in structured JSON format. {prompt}"}],
                response_format=CompanyAnalysis
            )
            return response.choices[0].message.parsed
        except Exception as e:
            print(f"GPT analysis failed for {company_name}: {str(e)}")
            return CompanyAnalysis(
                is_saas=False,
                growth_potential=0,
                risk_level=10,
                key_strengths=["Analysis failed"],
                concerns=["Analysis failed"],
                target_market="Unknown",
                competitive_advantage="Unknown"
            )

    def is_founded_recently(self, founded_year: int) -> bool:
        """Check if company was founded in the last 5 years"""
        return self.current_year - founded_year <= 5
    
    def has_valid_employee_count(self, employee_count: int) -> bool:
        """Check if company has 20-60 employees"""
        return 20 <= employee_count <= 60
    
    def is_north_american(self, headquarters: str) -> bool:
        """Check if company is headquartered in North America"""
        return any(country in headquarters for country in ['USA', 'Canada'])
    
    def is_mostly_north_american(self, locations: str) -> bool:
        """Check if majority of employees are in North America"""
        try:
            loc_dict = json.loads(locations.replace("'", '"'))
            total_employees = sum(loc_dict.values())
            na_employees = loc_dict.get('USA', 0) + loc_dict.get('Canada', 0)
            return (na_employees / total_employees) > 0.5
        except:
            return False
    
    def has_stable_growth(self, growth_2y: float, growth_1y: float, growth_6m: float) -> bool:
        """
        Check if company has stable growth
        Defined as:
        - All growth rates are positive
        - No extreme fluctuations (max/min ratio < 3)
        - Not declining over time
        """
        if pd.isna(growth_2y):  # Too new for 2Y data
            return growth_1y > growth_6m > 0
        
        rates = [growth_2y/2, growth_1y, growth_6m*2]  # Annualized rates
        if min(rates) <= 0:
            return False
        
        return max(rates) / min(rates) < 3

    def classify_companies(self) -> pd.DataFrame:
        """Classify companies based on all criteria including GPT analysis"""
        results = []
        
        for _, company in self.df.iterrows():
            # Get GPT analysis
            gpt_analysis = self.get_gpt_analysis(
                company['Company Name'],
                company['Description'],
                company['Industry']
            )
            
            # Basic criteria
            basic_criteria_met = (
                self.is_founded_recently(company['Founded Year']) and
                self.has_valid_employee_count(company['Total Employees']) and
                self.is_north_american(company['Headquarters']) and
                self.is_mostly_north_american(company['Employee Locations']) and
                self.has_stable_growth(
                    company['Employee Growth 2Y (%)'],
                    company['Employee Growth 1Y (%)'],
                    company['Employee Growth 6M (%)']
                )
            )
            
            # Advanced criteria from GPT
            advanced_criteria_met = (
                gpt_analysis.is_saas and
                gpt_analysis.growth_potential >= 7 and
                gpt_analysis.risk_level <= 6
            )
            
            interesting = basic_criteria_met and advanced_criteria_met
            
            results.append({
                'Company Name': company['Company Name'],
                'Founded Year': company['Founded Year'],
                'Total Employees': company['Total Employees'],
                'Headquarters': company['Headquarters'],
                'Industry': company['Industry'],
                'Growth Potential': gpt_analysis.growth_potential,
                'Risk Level': gpt_analysis.risk_level,
                'Key Strengths': ', '.join(gpt_analysis.key_strengths),
                'Concerns': ', '.join(gpt_analysis.concerns),
                'Target Market': gpt_analysis.target_market,
                'Competitive Advantage': gpt_analysis.competitive_advantage,
                'Interesting': 'Yes' if interesting else 'No'
            })
            
        return pd.DataFrame(results)

def main():
    # Get OpenAI API key from environment variable
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    classifier = CompanyClassifier('data/data.csv', openai_key)
    results = classifier.classify_companies()
    
    # Save detailed results to CSV
    results.to_csv('classified_companies_detailed.csv', index=False)
    
    # Print summary statistics
    total = len(results)
    interesting = sum(results['Interesting'] == 'Yes')
    print(f"\nClassification Results:")
    print(f"Total companies analyzed: {total}")
    print(f"Interesting companies: {interesting}")
    print(f"Percentage interesting: {(interesting/total)*100:.1f}%")
    
    # Print interesting companies with details
    print("\nInteresting Companies:")
    interesting_companies = results[results['Interesting'] == 'Yes']
    for _, company in interesting_companies.iterrows():
        print(f"\n- {company['Company Name']} ({company['Industry']})")
        print(f"  Growth Potential: {company['Growth Potential']}/10")
        print(f"  Risk Level: {company['Risk Level']}/10")
        print(f"  Key Strengths: {company['Key Strengths']}")
        print(f"  Competitive Advantage: {company['Competitive Advantage']}")

if __name__ == "__main__":
    main()
