## Setup Instructions

1. Install Python Requirements
   ```bash
   pip install -r requirements.txt
   ```

2. Configure OpenAI API Key
   - Add your OpenAI API key:
     ```
    $ export OPENAI_API_KEY=your_api_key_here
     ```
   - Replace `your_api_key_here` with your actual OpenAI API key
   - Note: Never commit your API key to version control

3. Run the Application
   ```bash
   python main.py -i <input_file.csv> -o <output_file.csv>
   ```

   Arguments:
   - `-i, --input`: Path to input CSV file containing company data
     - Required columns: Company Name, Founded Year, Total Employees, Headquarters, Industry, Description
   
   - `-o, --output`: Path where the output CSV file will be saved
     - Contains: Basic company info, growth potential, risk assessments, key strengths, and classification results
   
   - `-h, --help`: Show detailed help message and exit

   Example:
   ```bash
   python main.py -i companies.csv -o analysis_results.csv
   ```

## Requirements
- Python 3.7+
- OpenAI API key
- Required Python packages are listed in `requirements.txt`

## Note
Make sure to keep your OpenAI API key secure and never share it publicly.
