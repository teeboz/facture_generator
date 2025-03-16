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
    <title>Générateur de Facture</title>
</head>
<body>
    <h1>Générer une Facture</h1>
    <form method="POST" action="/generate-invoice">
        <fieldset>
            <legend>Informations de l'entreprise</legend>
            Nom de l'entreprise: <input type="text" name="company_name" value="Entreprise Nadine"><br>
            Adresse: <input type="text" name="company_address" value="Rue de l'Exemple, 123"><br>
            Téléphone: <input type="text" name="company_phone" value="+33 1 23 45 67 89"><br>
            Email: <input type="text" name="company_email" value="contact@nadine-entreprise.fr"><br>
            NIF: <input type="text" name="company_nif" value="XYZ123456789"><br>
        </fieldset>
        <br>
        <fieldset>
            <legend>Informations du client</legend>
            Nom du client: <input type="text" name="client_name" value="Nadine Imoma"><br>
            Adresse du client: <input type="text" name="client_address" value="Av. Sierra Calderona 29A"><br>
            NIF client: <input type="text" name="client_nif" value="Y9912567H"><br>
        </fieldset>
        <br>
        <fieldset>
            <legend>Informations de la facture</legend>
            N° Facture: <input type="text" name="invoice_number" value="2025/05"><br>
            Date (JJ/MM/AAAA): <input type="text" name="invoice_date" value="{{today}}"><br>
            Mode de paiement: <input type="text" name="payment_method" value="Transférencia bancaria"><br>
        </fieldset>
        <br>
        <fieldset>
            <legend>Articles</legend>
            (Pour la démo, on gère un seul article)<br>
            Description: <input type="text" name="item_description" value="Installation électrique"><br>
            Quantité: <input type="text" name="item_qty" value="1"><br>
            Prix unitaire: <input type="text" name="item_price" value="465.00"><br>
        </fieldset>
        <br>
        <input type="submit" value="Générer la Facture PDF">
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
    company_info = {
        "name": request.form.get("company_name", ""),
        "address": request.form.get("company_address", ""),
        "phone": request.form.get("company_phone", ""),
        "email": request.form.get("company_email", ""),
        "nif": request.form.get("company_nif", "")
    }
    client_info = {
        "name": request.form.get("client_name", ""),
        "address": request.form.get("client_address", ""),
        "nif": request.form.get("client_nif", "")
    }
    invoice_data = {
        "invoice_number": request.form.get("invoice_number", ""),
        "invoice_date": request.form.get("invoice_date", ""),
        "payment_method": request.form.get("payment_method", ""),
        "additional_info": "Le paiement de cette facture se peut réaliser par virement."
    }

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
        download_name="facture.pdf",
        mimetype="application/pdf"
    )

def create_pdf(company_info, client_info, invoice_data, items):
    class InvoicePDF(FPDF):
        def header(self):
            # Utilise DejaVu pour l'en-tête
            self.set_font('DejaVu', '', 16)
            self.cell(0, 10, "FACTURE", ln=True, align='C')
            self.ln(5)
            self.set_line_width(0.5)
            self.set_draw_color(0, 0, 0)
            self.line(10, 25, 200, 25)
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            # Utilise DejaVu pour le pied de page (8 points)
            self.set_font('DejaVu', '', 8)
            page = f"Page {self.page_no()}/{{nb}}"
            self.cell(0, 10, page, 0, 0, 'C')

    # Création de l'instance PDF
    pdf = InvoicePDF()

    # IMPORTANT : Ajoutez les polices avant d'appeler add_page() car header() en a besoin.
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)

    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("DejaVu", "", 12)

    # -- Infos Société --
    pdf.cell(100, 5, company_info["name"], ln=True)
    pdf.multi_cell(100, 5, company_info["address"])
    pdf.cell(100, 5, f"Téléphone : {company_info['phone']}", ln=True)
    pdf.cell(100, 5, f"E-mail : {company_info['email']}", ln=True)
    pdf.cell(100, 5, f"NIF : {company_info['nif']}", ln=True)
    pdf.ln(5)

    # -- Infos Facture --
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(40, 5, "Facture N° : ", ln=False)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(40, 5, invoice_data["invoice_number"], ln=True)

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(40, 5, "Date : ", ln=False)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(40, 5, invoice_data["invoice_date"], ln=True)

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(40, 5, "Mode de paiement : ", ln=False)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(40, 5, invoice_data["payment_method"], ln=True)
    pdf.ln(5)

    # -- Infos Client --
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(40, 5, "Client : ", ln=True)
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(100, 5, client_info["name"], ln=True)
    pdf.multi_cell(100, 5, client_info["address"])
    pdf.cell(100, 5, f"NIF : {client_info['nif']}", ln=True)
    pdf.ln(5)

    # -- Tableau des articles --
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(80, 8, "Description", border=1, align='C', fill=True)
    pdf.cell(30, 8, "Quantité", border=1, align='C', fill=True)
    pdf.cell(40, 8, "Prix Unitaire", border=1, align='C', fill=True)
    pdf.cell(40, 8, "Montant", border=1, align='C', fill=True)
    pdf.ln(8)

    pdf.set_font("DejaVu", "", 12)
    subtotal = 0.0
    tva_rate = 0.21
    for item in items:
        description = item["description"]
        qty = item["qty"]
        price = item["price"]
        line_total = qty * price
        subtotal += line_total

        pdf.cell(80, 8, description, border=1)
        pdf.cell(30, 8, f"{qty}", border=1, align='C')
        pdf.cell(40, 8, f"{price:.2f} €", border=1, align='R')
        pdf.cell(40, 8, f"{line_total:.2f} €", border=1, align='R')
        pdf.ln(8)

    tva_amount = subtotal * tva_rate
    total = subtotal + tva_amount

    pdf.ln(5)
    pdf.cell(150, 8, "Sous-total :", border=0, align='R')
    pdf.cell(40, 8, f"{subtotal:.2f} €", border=0, align='R')
    pdf.ln(5)
    pdf.cell(150, 8, f"TVA ({int(tva_rate*100)}%) :", border=0, align='R')
    pdf.cell(40, 8, f"{tva_amount:.2f} €", border=0, align='R')
    pdf.ln(5)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(150, 8, "Total à payer :", border=0, align='R')
    pdf.cell(40, 8, f"{total:.2f} €", border=0, align='R')
    pdf.ln(10)

    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 5, invoice_data["additional_info"])

    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

if __name__ == "__main__":
    app.run(debug=True)
