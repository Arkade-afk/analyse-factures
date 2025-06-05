from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import pdfplumber
import io

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

def extract_data_from_pdf(fichier_bytes):
    with pdfplumber.open(io.BytesIO(fichier_bytes)) as pdf:
        texte_total = ""
        for page in pdf.pages:
            texte_total += page.extract_text() + "\n"

    lignes = texte_total.splitlines()
    articles = []
    for ligne in lignes:
        if any(mot in ligne.lower() for mot in ["bosch", "makita", "visseuse", "perceuse"]):
            try:
                nom = ligne.rsplit(" ", 1)[0]
                prix = float(ligne.rsplit(" ", 1)[1].replace(",", "."))
                articles.append({"nom": nom, "prix_facture": prix})
            except:
                continue

    return {
        "societe": "FournisseurA",
        "articles": articles
    }

def comparer_prix(data_facture, identifiant, mot_de_passe):
    resultats = []
    for article in data_facture["articles"]:
        nom = article["nom"]
        prix_facture = article["prix_facture"]
        prix_site_fournisseur = prix_facture * 0.95
        prix_partenaire = prix_facture * 0.90

        resultats.append({
            "article": nom,
            "prix_facture": prix_facture,
            "prix_site_fournisseur": prix_site_fournisseur,
            "prix_partenaire": prix_partenaire,
            "ecart_fournisseur": prix_facture - prix_site_fournisseur,
            "ecart_partenaire": prix_facture - prix_partenaire
        })

    return {
        "societe": data_facture["societe"],
        "comparaison": resultats
    }

@app.post("/analyser-facture/")
async def analyser_facture(
    pdf: UploadFile,
    identifiant: str = Form(...),
    mot_de_passe: str = Form(...),
):
    contenu = await pdf.read()
    data_facture = extract_data_from_pdf(contenu)
    resultat = comparer_prix(data_facture, identifiant, mot_de_passe)
    return JSONResponse(content=resultat)

if __name__ == "__main__":
    uvicorn.run("app:app", port=8000, reload=True)
