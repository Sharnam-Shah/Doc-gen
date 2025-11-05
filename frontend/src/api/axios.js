import axios from 'axios';

const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL ||   'http://localhost:8000/api/', // Your backend URL
        timeout: 10000, // Optional: timeout after 10 seconds
    headers: {
        'Content-Type': 'application/json',
    }
});

export default instance;
