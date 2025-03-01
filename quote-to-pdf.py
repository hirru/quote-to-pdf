import os
import json
import streamlit as st
from fillpdf import fillpdfs  # Assuming this is the correct library name
from io import BytesIO
import tempfile  # Import tempfile here

def fill_pdf_form(pdf_file, json_data):
    """Fill PDF form fields with JSON data using fillpdfs."""
    try:
        # Create a temporary file to save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
            temp.write(pdf_file.getvalue())
            temp_path = temp.name

        # Get the form fields from the PDF for debugging
        fields = fillpdfs.get_form_fields(temp_path)

        # Map JSON data to PDF form fields (using field names from fillpdfs output)
        field_mapping = {
            "Please Initial Here": "Initial value",
            "FOR INTERNAL USE ONLY": "FOR INTERNAL USE ONLY value" ,
            "//Contract/CustomerName": json_data.get("CustomerName", ""),
            "//ContactDetail/FullName#1": json_data.get("ContactName", ""),
            "//ContractAccountDetails/ContractAccountDetail[1]/Street": json_data.get("ServiceAddress", ""),
            "//ContractAccountDetails/ContractAccountDetail[1]/City": json_data.get("City", ""),
            "//ContractAccountDetails/ContractAccountDetail[1]/StateName": json_data.get("State", ""),
            "//ContractAccountDetails/ContractAccountDetail[1]/ZIP": json_data.get("ZipCode", ""),
            "//BillingAddress/AddressLine1": json_data.get("MailingAddress", ""),
            "//BillingAddress/City": json_data.get("City", ""),  # Assuming Mailing City is same as City; adjust if different
            "//BillingAddress/StateName": json_data.get("State", ""),  # Assuming Mailing State is same as State; adjust if different
            "//BillingAddress/ZIP": json_data.get("ZipCode", ""),  # Assuming Mailing Zip is same as Zip; adjust if different
            # Handle multiple /Contract/AccountData fields by creating unique mappings if needed
            "//ContractAccountDetails/ContractAccountDetail[1]/Utility": json_data.get("UtilityProvider", ""),  # For Utility (adjust field name if needed)
            "//ContractAccountDetails/ContractAccountDetail[1]/AccountNumber": json_data.get("AccountNumber", ""),  # For Account Number
            "//ContractAccountDetails/ContractAccountDetail[1]/MeterNumber": json_data.get("MeterNumber", ""),  # For Meter Number
            "//Contract/Phone": json_data.get("PhoneNumber", ""),
            "//ContactDetail/EmailWork": json_data.get("Email", ""),
            "//PrepareDateFormat#1": json_data.get("Date", ""),
            "//ContractStartDate/MonthName": "Yes" if json_data.get("AgreementCheckbox1", False) else "Off",  # Try "Yes"/"Off" for checkbox
            "//Contract/Term": json_data.get("ContractTerm", ""),
            "//Contract/PriceQuoted": json_data.get("QuotedPrice", ""),
            "By": json_data.get("QuotedPrice", ""),
            "//bool1": "Yes",
            "//bool2": "Yes",
            "FOR INTERNAL USE ONLY_2": json_data.get("QuotedPrice", ""),
            # Adjust field names and values based on fillpdfs.get_form_fields() output
        }

        # Filter field_mapping to only include fields that exist in the PDF
        valid_fields = {k: v for k, v in field_mapping.items() if k in fields}
        print("valid fields", field_mapping)

        # Fill the PDF with the mapped data
        output_pdf = "filled.pdf"
        fillpdfs.write_fillable_pdf(temp_path, output_pdf, field_mapping)

        # Flatten the PDF (optional, for non-editable output)
        flattened_pdf = "filled_flat.pdf"
        fillpdfs.flatten_pdf(output_pdf, flattened_pdf)

        # Read the flattened PDF into a BytesIO object for download
        with open(flattened_pdf, "rb") as f:
            filled_pdf = BytesIO(f.read())
        filled_pdf.seek(0)

        # Clean up temporary files
        for file in [temp_path, output_pdf, flattened_pdf]:
            if os.path.exists(file):
                os.remove(file)

        return filled_pdf

    except Exception as e:
        # Clean up temporary files if an error occurs
        for file in [temp_path] if 'temp_path' in locals() else []:
            if os.path.exists(file):
                os.remove(file)
        raise Exception(f"PDF form filling failed: {str(e)}")

def main():
    st.set_page_config(page_title="PDF Form Filler", layout="wide")
    
    st.title("📄 PDF Form Filler")
    st.markdown("Upload a PDF and provide JSON data to fill form fields")
    
    # Create two columns for inputs
    col1, col2 = st.columns(2)
    
    # PDF Upload in first column
    st.subheader("Upload PDF Document")
    uploaded_pdf = st.file_uploader("Choose a PDF file", type="pdf", help="Upload a fillable PDF document")
    
    # JSON input in second column
    st.subheader("Enter Form Data (JSON)")
    default_json = '''{
  "CustomerName": "John Doe",
  "ContactName": "Jane Doe",
  "ServiceAddress": "123 Main Street",
  "City": "Chicago",
  "State": "IL",
  "ZipCode": "60601",
  "MailingAddress": "456 Elm Street",
  "AccountNumber": "123456789",
  "UtilityProvider": "Nicor Gas",
  "MeterNumber": "987654321",
  "PhoneNumber": "+1-312-555-6789",
  "Email": "john.doe@example.com",
  "Date": "2025-03-01",
  "ContractTerm": "24 months",
  "QuotedPrice": "0.55 per therm",
  "AgreementCheckbox1": true
}'''
        
    json_input = st.text_area("JSON Data", value=default_json, height=250)
    
    # Generate button
    if st.button("🔄 Fill PDF", type="primary"):
        if not uploaded_pdf or not json_input:
            st.error("Please upload a PDF and provide JSON data")
            return
        
        try:
            # Validate JSON format
            json_data = json.loads(json_input)
            
            # Validate required fields
            required_fields = ["CustomerName", "ServiceAddress", "City", "State", "ZipCode", "PhoneNumber", "Email"]
            missing_fields = [field for field in required_fields if field not in json_data or not json_data[field]]
            if missing_fields:
                st.error(f"Missing or empty required fields: {', '.join(missing_fields)}")
                return
            
            with st.spinner("Filling PDF form..."):
                # Fill the PDF with JSON data
                filled_pdf = fill_pdf_form(uploaded_pdf, json_data)
                
                # Provide download link
                st.download_button(
                    label="📥 Download Filled PDF",
                    data=filled_pdf,
                    file_name="filled_constellation_form.pdf",
                    mime="application/pdf"
                )
                
                st.success("✨ PDF filled successfully!")
                
        except json.JSONDecodeError as je:
            st.error(f"Invalid JSON format: {str(je)}\nPlease check your input for syntax errors.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()