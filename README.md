# EpubConsolidator2

**EpubConsolidator2** is a Python tool that consolidates EPUB files into organized text files by chapter.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/mateogon/EpubConsolidator2.git
   cd EpubConsolidator2
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Add EPUB Files**

   - Place your EPUB files in the `epub_files/` directory.

2. **Run the Script**

   ```bash
   python extract_text.py
   ```

3. **View Extracted Text**

   - The extracted text files will be available in the `extracted_text/` directory, organized by book and chapter.

## Git Configuration

- The `.gitignore` is set to ignore extracted text files while keeping the folder structure.

## License

This project is licensed under the [MIT License](LICENSE).
