# CB-1.0.1 — Local widget preview

The `/widget/embed` endpoint renders the Tilda template against the origin of the
current request. Local development therefore loads JavaScript, CSS and the sales
API from `http://127.0.0.1:8000`, while the source Tilda template retains the
`https://YOUR-API-DOMAIN` placeholder for production deployment.
