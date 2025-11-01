import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const navigate = useNavigate();
  const [role, setRole] = useState('patient');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    // Basic validation
    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/users/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password
          // Note: Removed role from login request as backend doesn't use it
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Login failed');
      }

      // Store token and user data
      if (data.token) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('userRole', data.user.role);
        localStorage.setItem('userData', JSON.stringify(data.user));
      }

      // Navigate based on user's actual role from backend
      switch(data.user.role) {
        case 'patient': navigate('/patient'); break;
        case 'doctor': navigate('/doctor'); break;
        case 'lab': navigate('/lab'); break;
        default: navigate('/login');
      }
    } catch (error) {
      setError(error.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLogin();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">Good to see you again</h2>
        </div>

        {/* Login Form */}
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200">
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {/* Email Field */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your email
            </label>
            <input 
              type="email"
              placeholder="e.g. elon@tesla.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent placeholder-gray-400"
            />
          </div>

          {/* Password Field */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your password
            </label>
            <input 
              type="password"
              placeholder="e.g. llovemangools123"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent placeholder-gray-400"
            />
          </div>

          {/* Sign In Button */}
          <button 
            onClick={handleLogin}
            disabled={loading}
            className="w-full bg-black text-white py-3 px-4 rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>

          {/* Links */}
          <div className="mt-6 text-center space-y-2">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <span 
                className="text-green-600 hover:text-green-700 cursor-pointer font-medium"
                onClick={() => navigate('/register')}
              >
                Register
              </span>
            </p>
            <p className="text-sm text-gray-600">
              <span className="cursor-pointer hover:text-gray-800">
                Forgot password?
              </span>
            </p>
          </div>
        </div>

        {/* Footer - Medical Portal Services */}
        <div className="text-center">
          <div className="border-t border-gray-200 pt-8">
            <div className="text-sm text-gray-500 mb-4">Medical Portal</div>
            <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-600">
              <span>Patient Portal</span>
              <span className="font-semibold text-gray-900">Doctor Portal</span>
              <span>Lab Portal</span>
              <span>Admin Portal</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;