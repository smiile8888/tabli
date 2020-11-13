# TabHeart
Fast Chrome extension tab filtering and search using BlobHeart

## Install

### Extension
1. Node and npm
2. `npm install`

### Backend
1. Python3
2. `pip3 install -r backend/requirements.txt`

## Get Start

### Extension
1. `npm run build-dev`
2. `npm run watch`

### Test extension
1. Go to Chrome and go to `chrome://extensions`
2. Click `Load unpacked`
3. Select the `build/` directory

### Backend
1. `python3 backend/app.py`

### To push changes
**WARNING:** There is a test in the original code, to avoid it using
```
    git commit -n (or --no-verify) -m "your_message"
```

## Disclaimer

The original codebase is from [Tabli](http://antonycourtney.github.io/tabli/). Thanks Antony!