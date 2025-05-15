# GENAI-BRD-FUNCTIONS-1

Python Cloud Functions that connect to external Firebase emulators.

## Overview

This repository contains standalone Google Cloud Functions in Python that connect to Firebase emulators running in a separate project. The functions use the `BaseFunction` pattern for consistent structure.

## Functions

- `process_image`: Processes images uploaded to Firebase Storage
- `cleanup_resources`: Cleans up unused resources in Storage and Firestore
- `hello_world`: Simple demo function that demonstrates connectivity

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 16+
- Firebase CLI
- A separate Firebase project with emulators running

### Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/genai-brd-functions-1.git
   cd genai-brd-functions-1
   ```

2. Install Python dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies:
   ```
   npm install
   ```

### Running the Functions

1. Start the Firebase emulators in your main app repository:

   ```
   cd ../firebase-app-repo
   firebase emulators:start
   ```

2. In a new terminal, set up environment variables and start a function:

   ```
   cd genai-brd-functions-1
   source dev.sh
   npm run dev
   ```

3. To debug, press F5 in VS Code to attach the debugger to the running function.

### Available npm Scripts

- `npm run dev` - Start the `process_image` function with debugger enabled
- `npm run dev:hello` - Start the `hello_world` function with debugger enabled
- `npm run dev:cleanup` - Start the `cleanup_resources` function with debugger enabled
- `npm start` - Start the `process_image` function without nodemon or debugging

## Project Structure

```
.
├── src/
│   ├── common/base.py         # Base class for all functions
│   ├── func_image/main.py     # process_image function
│   ├── func_cleanup/main.py   # cleanup_resources function
│   └── func_hello/main.py     # hello_world function
├── .vscode/
│   ├── launch.json            # Debug config (attaches to port 9229)
│   └── settings.json          # Python path hints
├── dev.sh                     # Sets up emulator environment variables
├── package.json               # Node.js config and scripts
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment variables
├── .gitignore
└── README.md
```

## Environment Variables

The following environment variables are set by `dev.sh` to connect to the emulators:

```
FIRESTORE_EMULATOR_HOST=localhost:8090
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
FIREBASE_STORAGE_EMULATOR_HOST=localhost:9199
PUBSUB_EMULATOR_HOST=localhost:8085
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
