import httpx, io

pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n5 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td (Hello Test PDF) Tj ET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000266 00000 n \n0000000339 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n433\n%%EOF"

r = httpx.post("https://examai-hub-api.onrender.com/auth/register", json={"email": "up2@t.com", "username": "up2", "password": "up2test12"}, timeout=20)
t = r.json()["access_token"]
print("Auth OK")

files = {"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
r2 = httpx.post("https://examai-hub-api.onrender.com/upload/pdf", headers={"Authorization": f"Bearer {t}"}, files=files, timeout=30)
print(f"Upload status: {r2.status_code}")
if r2.status_code == 200:
    d = r2.json()
    print(f"  Pages: {d.get('pages','?')}")
    print(f"  Words: {d.get('words','?')}")
    print(f"  Doc: {d.get('document_id','?')[:15]}")
    print(f"  Method: {d.get('extraction_method','?')}")
    print("UPLOAD WORKS!")
else:
    print(f"  Error: {r2.text[:300]}")
