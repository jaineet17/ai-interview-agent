import axios from 'axios';

const API_BASE_URL = '/api';

// Create an axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Function to handle file uploads
export const uploadFile = async (file: File, type: 'job' | 'company' | 'candidate'): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await api.post(`/upload/${type}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    handleApiError(error);
    throw error;
  }
};

// Function to upload all files at once
export const uploadCustomData = async (
  jobFile: File, 
  companyFile: File, 
  candidateFile: File
): Promise<any> => {
  const formData = new FormData();
  formData.append('job_file', jobFile);
  formData.append('company_file', companyFile);
  formData.append('candidate_file', candidateFile);
  
  try {
    const response = await api.post('/upload_custom_data', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    handleApiError(error);
    throw error;
  }
};

// Function to load sample data
export const loadSampleData = async (): Promise<any> => {
  try {
    const response = await api.post('/load_sample_data');
    return response.data;
  } catch (error) {
    handleApiError(error);
    throw error;
  }
};

// Function to initialize interview
export const initializeInterview = async (demoMode: boolean = false): Promise<any> => {
  try {
    const response = await api.post('/initialize_interview', { demo_mode: demoMode });
    return response.data;
  } catch (error) {
    handleApiError(error);
    throw error;
  }
};

// Function to start interview
export const startInterview = async (): Promise<any> => {
  try {
    const response = await api.post('/start_interview');
    
    // Check if there's an error in the response
    if (response.data && response.data.status === 'error') {
      throw new Error(response.data.error || 'Failed to start interview');
    }
    
    return response.data;
  } catch (error) {
    handleApiError(error);
    throw error;
  }
};

// Function to process response
export const processResponse = async (responseText: string): Promise<any> => {
  try {
    const response = await api.post('/process_response', { response: responseText });
    
    // Check if there's an error in the response
    if (response.data && response.data.status === 'error') {
      throw new Error(response.data.error || 'Failed to process response');
    }
    
    return response.data;
  } catch (error) {
    handleApiError(error);
    throw error;
  }
};

// Function to extract text from files
export const extractTextFromFile = async (file: File): Promise<string> => {
  // For client-side text extraction from common file types
  if (file.type === 'application/pdf') {
    // For PDF files, we'd need to use a library like pdf-parse
    // This would be implemented here
    throw new Error('PDF extraction not implemented in this example');
  } else if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    // For DOCX files, we'd need to use a library like mammoth or docx
    // This would be implemented here
    throw new Error('DOCX extraction not implemented in this example');
  } else if (file.type === 'text/plain' || file.type === 'application/json') {
    // For text and JSON files, we can just read them directly
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  } else {
    throw new Error(`Unsupported file type: ${file.type}`);
  }
};

// Error handling function
const handleApiError = (error: any): void => {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data;
    console.error('API Error:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: responseData,
    });
  } else {
    console.error('Unexpected error:', error);
  }
};

export default api; 