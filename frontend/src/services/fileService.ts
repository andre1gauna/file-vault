// frontend/src/services/files.ts
import axios from 'axios';
import { File as FileType } from '../types/file';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export const fileService = {
  async uploadFile(file: File): Promise<FileType> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_URL}/files/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data as FileType;
  },

  async getFiles(): Promise<FileType[]> {
    const { data } = await axios.get<Page<FileType> | FileType[]>(`${API_URL}/files/`);
    // Se vier paginado (DRF): use data.results; se vier array cru: retorne direto
    return Array.isArray(data) ? data : data.results ?? [];
  },

  async deleteFile(id: string | number): Promise<void> {
    await axios.delete(`${API_URL}/files/${id}/`);
  },

  async downloadFile(fileUrl: string, filename: string): Promise<void> {
    const response = await axios.get(fileUrl, { responseType: 'blob' });
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
