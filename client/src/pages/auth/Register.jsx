import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'patient',
    blockchainAddress: '',
    phone: '',
    dob: '',
    gender: 'other',
    address: '',
    specialty: '' // Added specialty field for doctors
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    if (error) setError('');
  };

  // Validate Ethereum address format
  const isValidEthereumAddress = (address) => {
    return /^0x[a-fA-F0-9]{40}$/.test(address);
  };

  const handleRegister = async () => {
    // Basic validation
    if (!formData.name || !formData.email || !formData.password || !formData.confirmPassword) {
      setError('Please fill the required fields: name, email and password');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password should be at least 6 characters');
      return;
    }

    // Doctor-specific validation
    if (formData.role === 'doctor') {
      if (!formData.blockchainAddress) {
        setError('Doctors must connect their Ethereum wallet');
        return;
      }
      
      if (!isValidEthereumAddress(formData.blockchainAddress)) {
        setError('Invalid Ethereum address format. Please connect your wallet again.');
        return;
      }

      if (!formData.specialty) {
        setError('Please specify your medical specialty');
        return;
      }
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const { confirmPassword, ...registerData } = formData;
      
      // Prepare payload based on role
      let payload = {
        name: registerData.name.trim(),
        email: registerData.email.trim().toLowerCase(),
        password: registerData.password,
        role: registerData.role,
        // Include optional fields only if they have values
        ...(registerData.phone && { phone: registerData.phone.trim() }),
        ...(registerData.dob && { dob: registerData.dob }),
        ...(registerData.gender && { gender: registerData.gender }),
        ...(registerData.address && { address: registerData.address.trim() }),
      };

      // Add role-specific fields
      if (registerData.role === 'doctor') {
        payload = {
          ...payload,
          blockchainAddress: registerData.blockchainAddress,
          specialty: registerData.specialty.trim()
        };
      } else {
        // For non-doctors, only include blockchainAddress if it exists and is valid
        if (registerData.blockchainAddress && isValidEthereumAddress(registerData.blockchainAddress)) {
          payload.blockchainAddress = registerData.blockchainAddress;
        }
      }

      console.log('Sending registration payload:', payload);
      console.log('User role:', payload.role);
      if (payload.role === 'doctor') {
        console.log('Doctor blockchain address:', payload.blockchainAddress);
        console.log('Doctor specialty:', payload.specialty);
      }
      
      const response = await fetch('http://localhost:5000/api/users/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      console.log('Registration response:', data);

      if (!response.ok) {
        throw new Error(data.message || `Registration failed: ${response.status}`);
      }

      if (!data.success) {
        throw new Error(data.message || 'Registration failed');
      }

      setSuccess(data.message || 'Registration successful! Redirecting to login...');
      
      // Clear form
      setFormData({
        name: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: 'patient',
        blockchainAddress: '',
        phone: '',
        dob: '',
        gender: 'other',
        address: '',
        specialty: ''
      });
      
      setTimeout(() => navigate('/login'), 2000);
      
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectWallet = async () => {
    setError('');
    setSuccess('');
    try {
      if (!window.ethereum) {
        setError('MetaMask (or another Ethereum wallet) not detected in your browser. Please install MetaMask to continue.');
        return;
      }

      // Check if already connected
      const accounts = await window.ethereum.request({ 
        method: 'eth_accounts' 
      });
      
      if (accounts && accounts.length > 0) {
        // Use existing account
        const address = accounts[0];
        if (isValidEthereumAddress(address)) {
          setFormData(prev => ({ 
            ...prev, 
            blockchainAddress: address 
          }));
          setSuccess(`Wallet connected: ${address.substring(0, 8)}...${address.substring(address.length - 6)}`);
          console.log('Wallet connected - Address:', address);
        } else {
          setError('Connected wallet address is invalid. Please try again.');
        }
        return;
      }

      // Request new connection
      const newAccounts = await window.ethereum.request({ 
        method: 'eth_requestAccounts' 
      });
      
      if (newAccounts && newAccounts.length > 0) {
        const address = newAccounts[0];
        if (isValidEthereumAddress(address)) {
          setFormData(prev => ({ 
            ...prev, 
            blockchainAddress: address 
          }));
          setSuccess(`Wallet connected: ${address.substring(0, 8)}...${address.substring(address.length - 6)}`);
          console.log('Wallet connected - Address:', address);
        } else {
          setError('Received invalid wallet address. Please try again.');
        }
      } else {
        setError('No accounts returned from wallet.');
      }
    } catch (err) {
      console.error('Wallet connect error:', err);
      if (err.code === 4001) {
        setError('Wallet connection was rejected. Please connect your wallet to continue.');
      } else {
        setError(err.message || 'Failed to connect wallet. Please try again.');
      }
    }
  };

  const handleDisconnectWallet = () => {
    console.log('Disconnecting wallet, previous address:', formData.blockchainAddress);
    setFormData(prev => ({ ...prev, blockchainAddress: '' }));
    setSuccess('Wallet disconnected');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleRegister();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">Create your account</h2>
          <p className="text-gray-600 mt-2">Join our secure medical platform</p>
        </div>

        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200">
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}
          
          {/* Success Message */}
          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
              <p className="text-green-600 text-sm">{success}</p>
            </div>
          )}

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Your full name *</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              onKeyPress={handleKeyPress}
              placeholder="e.g. Elon Musk"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Your email *</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              onKeyPress={handleKeyPress}
              placeholder="e.g. elon@tesla.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Phone number</label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="e.g. +1 555 555 5555"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date of birth</label>
              <input
                type="date"
                name="dob"
                value={formData.dob}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Gender</label>
            <select 
              name="gender" 
              value={formData.gender} 
              onChange={handleChange} 
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="prefer_not">Prefer not to say</option>
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
            <textarea
              name="address"
              value={formData.address}
              onChange={handleChange}
              placeholder="Street, City, State, ZIP"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
              rows={2}
            />
          </div>

          {/* Specialty Field - Only for Doctors */}
          {formData.role === 'doctor' && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Medical Specialty *</label>
              <input
                type="text"
                name="specialty"
                value={formData.specialty}
                onChange={handleChange}
                placeholder="e.g. Cardiology, Neurology, Pediatrics"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
                required
              />
            </div>
          )}

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Your password *</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              onKeyPress={handleKeyPress}
              placeholder="Minimum 6 characters"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Confirm password *</label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              onKeyPress={handleKeyPress}
              placeholder="Re-enter your password"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Role *</label>
            <select
              name="role"
              value={formData.role}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
              <option value="lab">Lab</option>
            </select>
          </div>

          {/* Blockchain Address Section */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ethereum Wallet Address 
              {formData.role === 'doctor' && <span className="text-red-500 ml-1">* Required for Doctors</span>}
            </label>
            
            {formData.blockchainAddress ? (
              <div className="space-y-2">
                <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-md">
                  <div className="flex-1">
                    <p className="text-sm font-mono text-green-800 break-all">
                      {formData.blockchainAddress}
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      {isValidEthereumAddress(formData.blockchainAddress) 
                        ? 'Valid Ethereum address ✓' 
                        : 'Invalid address format'}
                    </p>
                  </div>
                  <button
                    onClick={handleDisconnectWallet}
                    type="button"
                    className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
                  >
                    Disconnect
                  </button>
                </div>
                {!isValidEthereumAddress(formData.blockchainAddress) && formData.role === 'doctor' && (
                  <p className="text-xs text-red-600">
                    Please connect a valid Ethereum wallet address (0x...)
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <button
                  onClick={handleConnectWallet}
                  type="button"
                  className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-md hover:from-blue-700 hover:to-purple-700 transition-all font-medium flex items-center justify-center gap-2"
                >
                  <span>🔗</span>
                  Connect MetaMask Wallet
                </button>
                <p className="text-xs text-gray-500">
                  {formData.role === 'doctor' 
                    ? 'Required: Doctors must connect their Ethereum wallet to receive encrypted patient reports on the blockchain.'
                    : 'Optional: Connect your wallet for enhanced security features.'
                  }
                </p>
              </div>
            )}
          </div>

          <button
            onClick={handleRegister}
            disabled={loading}
            className="w-full bg-black text-white py-3 px-4 rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black font-medium disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Registering...</span>
              </div>
            ) : (
              'Create Account'
            )}
          </button>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <span
                className="text-blue-600 hover:text-blue-700 cursor-pointer font-medium"
                onClick={() => navigate('/login')}
              >
                Sign in
              </span>
            </p>
          </div>
        </div>

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

export default Register;