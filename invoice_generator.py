from flask import Flask, render_template_string, request, send_file
from fpdf import FPDF
import io
import datetime

app = Flask(__name__)

form_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>Invoice Generator</title>
</head>
<body>
    <h1>Generate an Invoice</h1>
    <form method="POST" action="/generate-invoice">
        <fieldset>
            <legend>Company Information</legend>
            Company Name: <input type="text" name="company_name" value="Nadine's Company"><br>
            Address: <input type="text" name="company_address" value="123 Example Street"><br>
            Phone: <input type="text" name="company_phone" value="+33 1 23 45 67 89"><br>
            Email: <input type="text" name="company_email" value="contact@nadine-company.com"><br>
            Tax ID: <input type="text" name="company_nif" value="XYZ123456789"><br>
        </fieldset>
        <br>
        <fieldset>
            <legend>Client Information</legend>
            Client Name: <input type="text" name="client_name" value="Nadine Imoma"><br>
            Client Address: <input type="text" name="client_address" value="Av. Sierra Calderona 29A"><br>
            Client Tax ID: <input type="text" name="client_nif" value="Y9912567H"><br>
        </fieldset>
        <br>
        <fieldset>
            <legend>Invoice Details</legend>
            Invoice #: <input type="text" name="invoice_number" value="2025/05"><br>
            Date (DD/MM/YYYY): <input type="text" name="invoice_date" value="{{today}}"><br>
            Payment Method: <input type="text" name="payment_method" value="Bank Transfer"><br>
        </fieldset>
        <br>
        <fieldset>
            <legend>Items</legend>
            (For the demo, we handle only one item)<br>
            Description: <input type="text" name="item_description" value="Electrical Installation"><br>
            Quantity: <input type="text" name="item_qty" value="1"><br>
            Unit Price: <input type="text" name="item_price" value="465.00"><br>
        </fieldset>
        <br>
        <input type="submit" value="Generate Invoice PDF">
    </form>
</body>
</html>
"""

@app.route('/')
def index():
    today = datetime.date.today().strftime("%d/%m/%Y")
    return render_template_string(form_template, today=today)

@app.route('/generate-invoice', methods=['POST'])
def generate_invoice():
    # Collect company info
    company_info = {
        "name": request.form.get("company_name", ""),
        "address": request.form.get("company_address", ""),
        "phone": request.form.get("company_phone", ""),
        "email": request.form.get("company_email", ""),
        "nif": request.form.get("company_nif", "")
    }
    # Collect client info
    client_info = {
        "name": request.form.get("client_name", ""),
        "address": request.form.get("client_address", ""),
        "nif": request.form.get("client_nif", "")
    }
    # Collect invoice details
    invoice_data = {
        "invoice_number": request.form.get("invoice_number", ""),
        "invoice_date": request.form.get("invoice_date", ""),
        "payment_method": request.form.get("payment_method", ""),
        "additional_info": "Payment for this invoice can be made by bank transfer."
    }
    # Collect item info
    try:
        qty = float(request.form.get("item_qty", "0"))
        price = float(request.form.get("item_price", "0"))
    except ValueError:
        qty = 0
        price = 0
    items = [
        {
            "description": request.form.get("item_description", ""),
            "qty": qty,
            "price": price
        }
    ]
    pdf_buffer = create_pdf(company_info, client_info, invoice_data, items)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="invoice.pdf",
        mimetype="application/pdf"
    )

def create_pdf(company_info, client_info, invoice_data, items):
    class InvoicePDF(FPDF):
        def header(self):
            # Draw a colored header background
            self.set_fill_color(0, 70, 127)  # Professional blue
            self.rect(0, 0, 210, 30, 'F')
            self.set_text_color(255, 255, 255)
            self.set_font('DejaVu', 'B', 24)
            self.cell(0, 30, "INVOICE", ln=True, align='C')
            self.set_text_color(0, 0, 0)
            self.ln(5)
        def footer(self):
            self.set_y(-15)
            self.set_font('DejaVu', '', 8)
            self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, 'C')
    
    pdf = InvoicePDF('P', 'mm', 'A4')
    # Load fonts (make sure the TTF files are in the same directory)
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("DejaVu", "", 12)
    
    # Company Info (top left)
    pdf.set_xy(10, 40)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(100, 6, company_info["name"], ln=True)
    pdf.set_font("DejaVu", "", 12)
    pdf.multi_cell(100, 5, company_info["address"])
    pdf.cell(100, 5, f"Phone: {company_info['phone']}", ln=True)
    pdf.cell(100, 5, f"Email: {company_info['email']}", ln=True)
    pdf.cell(100, 5, f"Tax ID: {company_info['nif']}", ln=True)
    
    # Invoice Details (top right)
    pdf.set_xy(120, 40)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(50, 6, "Invoice #:", ln=0)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(40, 6, invoice_data["invoice_number"], ln=True)
    
    pdf.set_xy(120, 48)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(50, 6, "Date:", ln=0)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(40, 6, invoice_data["invoice_date"], ln=True)
    
    pdf.set_xy(120, 56)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(50, 6, "Payment Method:", ln=0)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(40, 6, invoice_data["payment_method"], ln=True)
    pdf.ln(10)
    
    # Separator line
    pdf.set_line_width(0.5)
    pdf.line(10, 70, 200, 70)
    pdf.ln(10)
    
    # Client Info
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(100, 6, "Bill To:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(100, 5, client_info["name"], ln=True)
    pdf.multi_cell(100, 5, client_info["address"])
    pdf.cell(100, 5, f"Tax ID: {client_info['nif']}", ln=True)
    pdf.ln(10)
    
    # Items Table Header
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(80, 8, "Description", border=1, align='C', fill=True)
    pdf.cell(30, 8, "Qty", border=1, align='C', fill=True)
    pdf.cell(40, 8, "Unit Price", border=1, align='C', fill=True)
    pdf.cell(40, 8, "Amount", border=1, align='C', fill=True)
    pdf.ln(8)
    
    # Items List
    pdf.set_font("DejaVu", "", 12)
    subtotal = 0.0
    for item in items:
        qty = item["qty"]
        price = item["price"]
        line_total = qty * price
        subtotal += line_total
        
        pdf.cell(80, 8, item["description"], border=1)
        pdf.cell(30, 8, f"{qty}", border=1, align='C')
        pdf.cell(40, 8, f"{price:.2f} €", border=1, align='R')
        pdf.cell(40, 8, f"{line_total:.2f} €", border=1, align='R')
        pdf.ln(8)
    
    # Totals
    vat_rate = 0.21
    vat_amount = subtotal * vat_rate
    total = subtotal + vat_amount
    
    pdf.ln(5)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(150, 8, "Subtotal:", border=0, align='R')
    pdf.cell(40, 8, f"{subtotal:.2f} €", border=0, align='R')
    pdf.ln(8)
    
    pdf.cell(150, 8, f"VAT ({int(vat_rate*100)}%):", border=0, align='R')
    pdf.cell(40, 8, f"{vat_amount:.2f} €", border=0, align='R')
    pdf.ln(8)
    
    pdf.cell(150, 8, "Total Due:", border=0, align='R')
    pdf.cell(40, 8, f"{total:.2f} €", border=0, align='R')
    pdf.ln(10)
    
    # Additional Information
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 5, invoice_data["additional_info"])
    
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

if __name__ == "__main__":
    app.run(debug=True)
