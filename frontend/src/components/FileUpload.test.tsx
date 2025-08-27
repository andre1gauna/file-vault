import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FileUpload } from './FileUpload';
import { fileService } from '../services/fileService';

jest.mock('../services/fileService', () => ({
  fileService: {
    uploadFile: jest.fn(),
  },
}));

// Helper para renderizar com React Query Provider
const renderWithClient = (ui: React.ReactElement) => {
  const queryClient = new QueryClient();
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

// Silencia console.error para não poluir a saída
beforeAll(() => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
});
afterAll(() => {
  (console.error as jest.Mock).mockRestore();
});

describe('FileUpload component', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders upload form', () => {
    renderWithClient(<FileUpload onUploadSuccess={jest.fn()} />);
    expect(screen.getByText(/Upload File/i)).toBeInTheDocument();
    expect(screen.getByText(/Upload a file/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Upload/i })).toBeDisabled();
  });

  test('selects a file and enables upload button', () => {
    renderWithClient(<FileUpload onUploadSuccess={jest.fn()} />);
    const file = new File(['hello'], 'hello.txt', { type: 'text/plain' });

    const input = screen.getByLabelText(/Upload a file/i) as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText(/Selected: hello.txt/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Upload/i })).toBeEnabled();
  });

  test('upload button stays disabled when no file is selected', () => {
    renderWithClient(<FileUpload onUploadSuccess={jest.fn()} />);
    const button = screen.getByRole('button', { name: /Upload/i });
    expect(button).toBeDisabled();
  });

  test('successful upload calls service and onUploadSuccess', async () => {
    (fileService.uploadFile as jest.Mock).mockResolvedValue({});
    const onUploadSuccess = jest.fn();

    renderWithClient(<FileUpload onUploadSuccess={onUploadSuccess} />);
    const file = new File(['hello'], 'hello.txt', { type: 'text/plain' });

    const input = screen.getByLabelText(/Upload a file/i);
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: /Upload/i }));

    await waitFor(() => {
      expect(fileService.uploadFile).toHaveBeenCalledWith(file);
      expect(onUploadSuccess).toHaveBeenCalled();
    });
  });

  test('failed upload shows error message', async () => {
    (fileService.uploadFile as jest.Mock).mockRejectedValue(new Error('fail'));

    renderWithClient(<FileUpload onUploadSuccess={jest.fn()} />);
    const file = new File(['hello'], 'hello.txt', { type: 'text/plain' });

    const input = screen.getByLabelText(/Upload a file/i);
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: /Upload/i }));

    await waitFor(() => {
      expect(screen.getByText(/Failed to upload file/i)).toBeInTheDocument();
    });
  });

  test('shows loading spinner during upload', async () => {
    let resolveFn: Function;
    (fileService.uploadFile as jest.Mock).mockImplementation(
      () => new Promise((resolve) => (resolveFn = resolve))
    );

    renderWithClient(<FileUpload onUploadSuccess={jest.fn()} />);
    const file = new File(['hello'], 'hello.txt', { type: 'text/plain' });

    const input = screen.getByLabelText(/Upload a file/i);
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: /Upload/i }));

    expect(await screen.findByText(/Uploading/i)).toBeInTheDocument();

    // Finaliza a promise para liberar o estado
    resolveFn!({});
  });
});
