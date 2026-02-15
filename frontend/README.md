# Legalyze - AI-Powered Legal Contract Analysis

A professional, production-ready AI legal web application for contract analysis, risk detection, and digital signatures.

## 🎯 Features

- **Landing Page**: Marketing page with features, how it works, and CTA
- **Authentication**: Login and registration with JWT
- **Dashboard**: Role-based dashboard with stats, charts, and quick actions
- **Contract Upload**: Drag-and-drop file upload with progress tracking
- **Contract Analysis**: Detailed clause-by-clause analysis with risk detection
- **AI Suggestions**: Plain English explanations and improvement recommendations
- **Contract Generation**: AI-powered balanced contract generation
- **Contract Comparison**: Side-by-side comparison of two contracts
- **Digital Signature**: Legally binding electronic signatures
- **Profile & History**: User management and contract history
- **Admin Panel**: User management, audit logs, and system monitoring

## 🛠️ Tech Stack

- **Framework**: React.js with Vite
- **Styling**: Tailwind CSS v4
- **Routing**: React Router v7 (Declarative Mode)
- **State Management**: Redux Toolkit
- **API Client**: Axios
- **Charts**: Recharts
- **Icons**: Lucide React
- **UI Components**: HeadlessUI
- **Language**: JavaScript (no TypeScript)

## 📦 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── DashboardLayout.jsx
│   │   │   ├── Footer.jsx
│   │   │   ├── Navbar.jsx
│   │   │   └── Sidebar.jsx
│   │   └── ui/
│   │       ├── Badge.jsx
│   │       ├── Button.jsx
│   │       ├── Card.jsx
│   │       ├── Input.jsx
│   │       ├── Modal.jsx
│   │       ├── Select.jsx
│   │       └── Toast.jsx
│   ├── pages/
│   │   ├── AdminPage.jsx
│   │   ├── ComparePage.jsx
│   │   ├── ContractAnalysisPage.jsx
│   │   ├── Dashboard.jsx
│   │   ├── GeneratePage.jsx
│   │   ├── LandingPage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── ProfilePage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── SignaturePage.jsx
│   │   └── UploadPage.jsx
│   ├── router/
│   │   ├── index.jsx
│   │   └── ProtectedRoute.jsx
│   ├── store/
│   │   ├── authSlice.js
│   │   ├── contractsSlice.js
│   │   ├── index.js
│   │   └── uiSlice.js
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── index.html
├── package.json
└── vite.config.js
```

## 🚀 Getting Started

### Prerequisites

- Node.js v20.19+ or v22.12+
- npm, yarn, or pnpm

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to:
```
http://localhost:5173
```

### Demo Credentials

For testing the login functionality:
- **Email**: demo@legalyze.com
- **Password**: password123

## 🎨 Design System

### Colors

- **Primary**: Blue (#2563eb) - Professional, trustworthy
- **Grey Scale**: For neutral UI elements
- **Risk Colors**:
  - 🟢 Low Risk: Green (#10b981)
  - 🟡 Medium Risk: Yellow (#f59e0b)
  - 🔴 High Risk: Red (#ef4444)

### Typography

- **Font Family**: Inter (Google Fonts)
- **Font Weights**: 300, 400, 500, 600, 700

### Spacing

- xs: 0.25rem
- sm: 0.5rem
- md: 1rem
- lg: 1.5rem
- xl: 2rem
- 2xl: 3rem

## 🔒 Authentication & Authorization

- JWT-based authentication
- Role-based access control (Admin, Lawyer, Client)
- Protected routes using React Router
- Token stored in localStorage

## 📊 State Management

Redux Toolkit slices:
- **authSlice**: User authentication and profile
- **contractsSlice**: Contract management and upload
- **uiSlice**: UI state (modals, toasts, sidebar)

## 🧩 Reusable Components

All components follow HeadlessUI patterns:
- Fully accessible
- Keyboard navigation support
- Screen reader friendly
- Customizable with Tailwind classes

## 📱 Responsive Design

- Mobile-first approach
- Breakpoints: sm, md, lg, xl
- Sidebar collapses on mobile
- Touch-friendly UI elements

## 🚧 TODO / Future Enhancements

- [ ] Connect to real backend API
- [ ] Implement actual PDF/DOCX parsing
- [ ] Add real AI/ML integration
- [ ] Implement actual digital signature verification
- [ ] Add real-time collaboration features
- [ ] Implement email notifications
- [ ] Add export functionality (PDF/DOCX)
- [ ] Implement version control for contracts
- [ ] Add audit trail logging
- [ ] Implement dark mode

## 📄 License

Copyright © 2025 Legalyze. All rights reserved.

## 🤝 Contributing

This is a demo project. For production use, please implement proper backend integration and security measures.