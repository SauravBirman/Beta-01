# Beta-01

# Beta-01

A full-stack healthcare application with blockchain integration for secure medical records management.

## 🚀 Features

- **User Authentication & Authorization**: JWT-based secure authentication system
- **Medical Reports Management**: Upload, store, and manage medical reports
- **Blockchain Integration**: Secure data storage using Ethereum/blockchain technology
- **AI Integration**: AI-powered analysis capabilities
- **Doctor Management**: Connect with healthcare providers
- **IPFS Storage**: Decentralized file storage using IPFS

## 🛠️ Tech Stack

### Frontend (Client)
- **React 19** - Modern UI framework
- **React Router DOM** - Client-side routing
- **Tailwind CSS 4** - Utility-first CSS framework
- **Vite 7** - Fast build tool and dev server
- **ESLint** - Code quality and linting

### Backend (Server)
- **Node.js** with **Express 5** - Backend framework
- **MongoDB** with **Mongoose** - Database and ODM
- **Ethers.js** - Ethereum blockchain interaction
- **IPFS HTTP Client** - Decentralized file storage
- **JWT** - Authentication tokens
- **Bcrypt** - Password hashing
- **Multer** - File upload handling
- **Morgan** - HTTP request logging

### Development Tools
- **Hardhat** - Ethereum development environment
- **Nodemon** - Auto-reloading server
- **dotenv** - Environment variable management

## 📁 Project Structure

```
Beta-01/
├── client/                 # Frontend React application
│   ├── src/               # Source files
│   ├── public/            # Static assets
│   ├── package.json       # Frontend dependencies
│   └── vite.config.js     # Vite configuration
│
├── server/                # Backend Node.js application
│   ├── blockchain/        # Blockchain-related logic
│   ├── config/            # Configuration files
│   ├── controllers/       # Route controllers
│   ├── middlewares/       # Custom middleware
│   ├── models/            # Database models
│   ├── routes/            # API routes
│   │   ├── userRoutes.js
│   │   ├── reportRoutes.js
│   │   ├── aiRoutes.js
│   │   └── docRoutes.js
│   ├── utils/             # Utility functions
│   ├── views/             # View templates (if any)
│   ├── public/            # Public assets
│   ├── server.js          # Main server file
│   └── package.json       # Backend dependencies
│
└── README.md              # This file
```

## 🚦 Getting Started

### Prerequisites
- Node.js (v16 or higher)
- MongoDB (local or cloud instance)
- npm or yarn
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SauravBirman/Beta-01.git
   cd Beta-01
   ```

2. **Setup Backend**
   ```bash
   cd server
   npm install
   ```

   Create a `.env` file in the `server` directory:
   ```env
   PORT=5000
   MONGODB_URI=your_mongodb_connection_string
   JWT_SECRET=your_jwt_secret_key
   # Add other environment variables as needed
   ```

3. **Setup Frontend**
   ```bash
   cd ../client
   npm install
   ```

### Running the Application

1. **Start the Backend Server**
   ```bash
   cd server
   npm run dev      # Development mode with nodemon
   # or
   npm start        # Production mode
   ```
   Server will run on `http://localhost:5000` (or your configured PORT)

2. **Start the Frontend**
   ```bash
   cd client
   npm run dev      # Development mode
   ```
   Client will run on `http://localhost:5173` (default Vite port)

## 📡 API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check endpoint
- `/api/users` - User management endpoints
- `/api/reports` - Medical reports endpoints (protected)
- `/api/ai` - AI analysis endpoints
- `/api/doctors` - Doctor management endpoints

## 🔒 Authentication

The application uses JWT-based authentication. Protected routes require a valid JWT token in the request headers.

## 🧪 Development

### Frontend Development
```bash
cd client
npm run dev      # Start dev server
npm run build    # Build for production
npm run lint     # Run linter
npm run preview  # Preview production build
```

### Backend Development
```bash
cd server
npm run dev      # Start with nodemon
npm start        # Start normally
```

---
