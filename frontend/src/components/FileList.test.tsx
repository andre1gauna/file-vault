import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FileList } from '../components/FileList';
import { fileService } from '../services/fileService';

// 🔧 Mock do service
jest.mock('../services/fileService', () => ({
  fileService: {
    getFiles: jest.fn(),
    deleteFile: jest.fn(),
    downloadFile: jest.fn(),
  },
}));

// Helper para renderizar com React Query Provider
const renderWithClient = (ui: React.ReactElement) => {
  const queryClient = new QueryClient();
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe('FileList component', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading state (skeleton)', async () => {
    (fileService.getFiles as jest.Mock).mockReturnValue(new Promise(() => {})); // nunca resolve

    renderWithClient(<FileList />);
    // verifica se o skeleton está na tela
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  test('renders error state (fallback skeleton)', async () => {
    (fileService.getFiles as jest.Mock).mockRejectedValue(new Error('Network error'));

    renderWithClient(<FileList />);
    // em caso de erro, o componente ainda exibe skeleton
    await waitFor(() => {
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
    });
  });

  test('renders empty state', async () => {
    (fileService.getFiles as jest.Mock).mockResolvedValue([]);

    renderWithClient(<FileList />);
    await screen.findByText(/No files/i);
    expect(screen.getByText(/Get started by uploading a file/i)).toBeInTheDocument();
  });

  test('renders list of files and handles delete', async () => {
    const files = [
      {
        id: '1',
        original_filename: 'file1.txt',
        file_type: 'text/plain',
        size: 1024,
        uploaded_at: new Date().toISOString(),
        file: '/media/file1.txt',
      },
    ];
    (fileService.getFiles as jest.Mock).mockResolvedValue(files);
    (fileService.deleteFile as jest.Mock).mockResolvedValue({});

    renderWithClient(<FileList />);

    expect(await screen.findByText(/file1.txt/i)).toBeInTheDocument();

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(fileService.deleteFile).toHaveBeenCalledWith('1');
    });
  });

  test('handles file download', async () => {
    const files = [
      {
        id: '2',
        original_filename: 'file2.txt',
        file_type: 'text/plain',
        size: 2048,
        uploaded_at: new Date().toISOString(),
        file: '/media/file2.txt',
      },
    ];
    (fileService.getFiles as jest.Mock).mockResolvedValue(files);
    (fileService.downloadFile as jest.Mock).mockResolvedValue({});

    renderWithClient(<FileList />);

    expect(await screen.findByText(/file2.txt/i)).toBeInTheDocument();

    const downloadButton = screen.getByRole('button', { name: /download/i });
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(fileService.downloadFile).toHaveBeenCalledWith('/media/file2.txt', 'file2.txt');
    });
  });
});
