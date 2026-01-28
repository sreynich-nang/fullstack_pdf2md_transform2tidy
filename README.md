# About
A web UI application for extracting and processing PDF and image documents with a FastAPI backend offers a comprehensive solution for automatically extract tabular data from PDF documents, clean and normalize the extracted content, and transform it into structured, tidy datasets that follow Hadley Wickham’s Tidy Data principles.

![pic_eng](images/pic1.jpg)
---
---
![pic_eng](images/pic2.jpg)
---
---
![pic_eng](images/pic2_1.jpg)
---
---
![pic_eng](images/pic3.jpg)

## File Structure
```
fullstack_pdf2md_transform2tidy/
├── backend/
│   ├── Dockerfile
│   ├── environment.yml
│   └── app/main.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
└── docker-compose.yml
```

## Docker

- Check
  - `docker --version`
  - `docker compose version`
- Clone the Repository
  - `git clone https://github.com/sreynich-nang/fullstack_pdf2md_transform2tidy.git`
  - `cd fullstack_pdf2md_transform2tidy`
- Build and Start the App
  - `docker compose build`
  - `docker compose up`
- Visit the browser
  - Backend: `http://localhost:8000` or `http://localhost:8000/docs`
  - Frontend: `http://localhost:5555`
- Stop the App
  - `docker compose down` or "CTRL + C"
