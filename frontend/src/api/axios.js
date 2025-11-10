import axios from 'axios';

const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/',
    timeout: 120000, // Increased timeout to 120 seconds
    headers: {
        'Content-Type': 'application/json',
    },
    // Additional configuration for better network reliability
    validateStatus: status => status >= 200 && status < 500, // Don't reject if status < 500
    maxRedirects: 5,
    maxContentLength: 50 * 1024 * 1024, // 50MB max response size
});

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// Request interceptor
instance.interceptors.request.use(
    config => {
        // Add retry count to config
        config.retryCount = config.retryCount || 0;
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// Response interceptor with retry logic
instance.interceptors.response.use(
    response => response,
    async error => {
        const { config } = error;
        
        // If no config, or all retries exhausted, reject
        if (!config || !config.retryCount || config.retryCount >= MAX_RETRIES) {
            if (error.code === 'ECONNABORTED') {
                return Promise.reject(new Error('Request timed out. Please try again.'));
            }
            return Promise.reject(error);
        }

        // Increment retry count
        config.retryCount += 1;

        // Create new promise to handle delay
        const backoff = new Promise(resolve => {
            setTimeout(() => {
                resolve();
            }, RETRY_DELAY * config.retryCount); // Progressive delay
        });

        // Wait for backoff, then retry request
        await backoff;
        return instance(config);
    }
);

// Add custom method for document operations with extended timeout and retries
instance.documentOperation = async (url, method = 'get', data = null, customTimeout = 120000) => {
    let lastError = null;
    const maxRetries = 3;
    const baseDelay = 2000; // Start with 2 second delay

    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const config = {
                url,
                method,
                timeout: customTimeout || 120000, // Use custom timeout or default to 2 minutes
                headers: {
                    'Content-Type': 'application/json',
                },
                // Retry-specific headers
                'x-retry-attempt': attempt + 1
            };

            if (data) {
                config.data = data;
            }

            const response = await instance(config);
            
            // Check if response indicates success
            if (response.status >= 200 && response.status < 300) {
                return response;
            } else {
                throw new Error(`Request failed with status ${response.status}`);
            }
        } catch (error) {
            lastError = error;
            console.error(`Document operation error (attempt ${attempt + 1}/${maxRetries}):`, error);

            // Don't wait on the last attempt
            if (attempt < maxRetries - 1) {
                // Exponential backoff with jitter
                const delay = baseDelay * Math.pow(2, attempt) * (0.5 + Math.random());
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    // If we get here, all retries failed
    throw lastError || new Error('Operation failed after multiple retries');
};

export default instance;
