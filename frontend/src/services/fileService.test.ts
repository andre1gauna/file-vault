import axios from 'axios';
import { fileService } from './fileService';
import { File as FileType } from '../types/file';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('fileService', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('uploadFile sends FormData and returns file', async () => {
    const mockFile = new File(['hello'], 'test.txt', { type: 'text/plain' });
    const mockResponse: FileType = {
      id: '1',
      original_filename: 'test.txt',
      file_type: 'text/plain',
      size: 5,
      uploaded_at: new Date().toISOString(),
      file: '/media/test.txt',
    };

    mockedAxios.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await fileService.uploadFile(mockFile);

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.stringMatching(/\/files\/$/),
      expect.any(FormData),
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
    expect(result).toEqual(mockResponse);
  });

  test('getFiles returns array when API gives array', async () => {
    const mockFiles: FileType[] = [
      {
        id: '1',
        original_filename: 'a.txt',
        file_type: 'text/plain',
        size: 123,
        uploaded_at: new Date().toISOString(),
        file: '/media/a.txt',
      },
    ];

    mockedAxios.get.mockResolvedValueOnce({ data: mockFiles });

    const result = await fileService.getFiles();

    expect(mockedAxios.get).toHaveBeenCalledWith(expect.stringMatching(/\/files\/$/));
    expect(result).toEqual(mockFiles);
  });

  test('getFiles returns results when API gives paginated response', async () => {
    const mockFiles: FileType[] = [
      {
        id: '2',
        original_filename: 'b.txt',
        file_type: 'text/plain',
        size: 456,
        uploaded_at: new Date().toISOString(),
        file: '/media/b.txt',
      },
    ];

    mockedAxios.get.mockResolvedValueOnce({
      data: { count: 1, next: null, previous: null, results: mockFiles },
    });

    const result = await fileService.getFiles();

    expect(result).toEqual(mockFiles);
  });

  test('deleteFile calls axios.delete with correct url', async () => {
    mockedAxios.delete.mockResolvedValueOnce({});

    await fileService.deleteFile(123);

    expect(mockedAxios.delete).toHaveBeenCalledWith(expect.stringMatching(/\/files\/123\/$/));
  });

  test('downloadFile fetches blob and triggers download', async () => {
  const mockBlob = new Blob(['data']);
  mockedAxios.get.mockResolvedValueOnce({ data: mockBlob });

  // 🔧 Mock manual porque JSDOM não implementa
  // define se não existir
  if (!window.URL.createObjectURL) {
    (window.URL.createObjectURL as any) = jest.fn(() => 'blob-url');
  }
  if (!window.URL.revokeObjectURL) {
    (window.URL.revokeObjectURL as any) = jest.fn();
  }

  const createObjectURLSpy = jest.spyOn(window.URL, 'createObjectURL');
  const revokeObjectURLSpy = jest.spyOn(window.URL, 'revokeObjectURL');

  const appendChildSpy = jest
    .spyOn(document.body, 'appendChild')
    .mockImplementation((child: Node) => child);
  const removeChildSpy = jest
    .spyOn(document.body, 'removeChild')
    .mockImplementation((child: Node) => child);

  const clickMock = jest.fn();
  jest.spyOn(document, 'createElement').mockReturnValue({ click: clickMock } as any);

  await fileService.downloadFile('/media/file.txt', 'file.txt');

  expect(mockedAxios.get).toHaveBeenCalledWith('/media/file.txt', { responseType: 'blob' });
  expect(createObjectURLSpy).toHaveBeenCalled();
  expect(clickMock).toHaveBeenCalled();
  expect(revokeObjectURLSpy).toHaveBeenCalled();
  expect(appendChildSpy).toHaveBeenCalled();
  expect(removeChildSpy).toHaveBeenCalled();

  // restaura mocks
  createObjectURLSpy.mockRestore();
  revokeObjectURLSpy.mockRestore();
  appendChildSpy.mockRestore();
  removeChildSpy.mockRestore();
});

});
