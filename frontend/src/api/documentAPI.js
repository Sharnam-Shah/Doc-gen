import axios from 'axios';

class DocumentAPI {
    constructor() {
        this.client = axios.create({
            baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/',
            timeout: 120000,
            headers: {
                'Content-Type': 'application/json',
            },
            validateStatus: status => status >= 200 && status < 500,
            maxRedirects: 5,
            maxContentLength: 50 * 1024 * 1024,
            withCredentials: true,
        });

        // Add response interceptor for retries
        this.client.interceptors.response.use(
            response => response,
            async error => {
                const { config } = error;
                
                // Skip retry for specific status codes
                if (error.response && error.response.status === 404) {
                    return Promise.reject(error);
                }

                // Initialize retry count
                config.retryCount = config.retryCount || 0;
                
                // Maximum retry attempts
                const maxRetries = 3;
                
                if (config.retryCount >= maxRetries) {
                    return Promise.reject(error);
                }

                // Increase retry count
                config.retryCount += 1;

                // Calculate delay using exponential backoff
                const delay = Math.min(1000 * (2 ** config.retryCount) + Math.random() * 1000, 10000);

                await new Promise(resolve => setTimeout(resolve, delay));
                
                return this.client(config);
            }
        );
    }

    async createDocument(data) {
        try {
            const response = await this.client.post('conversations/', data);
            return response.data;
        } catch (error) {
            console.error('Error creating document:', error);
            throw error;
        }
    }

    async shareDocument(documentContent, title) {
        try {
            const response = await this.client.post('conversations/', {
                title: title || 'Shared Document',
                messages: [],
                initial_document_content: documentContent,
                notes: 'Shared document'
            });
            return response.data;
        } catch (error) {
            console.error('Error sharing document:', error);
            throw error;
        }
    }

    async getDocument(id) {
        try {
            const response = await this.client.get(`conversations/${id}`);
            return response.data;
        } catch (error) {
            console.error('Error fetching document:', error);
            throw error;
        }
    }
}

export const documentAPI = new DocumentAPI();