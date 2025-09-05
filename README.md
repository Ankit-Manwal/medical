# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

---

# Medical Condition Detector

## How to Run the Project

### 1. Start the Backend (Flask API)

Open a terminal and run the following commands:

```powershell
cd backend
pip install -r ../requirements.txt
python app.py
```

This will start the backend server at `http://127.0.0.1:5000`.

### 2. Start the React Frontend (Vite)

Open another terminal and run:

```powershell
npm install
npm run dev
```

This will start the frontend at `http://localhost:5173`.

---

The frontend is configured to proxy API requests to the backend automatically.
