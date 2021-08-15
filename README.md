BYBT telegram bot
===

## How to use.
1. Install dependencies
```bash
git clone https://github.com/racterub/bybtbot
cd bybtbot
pipenv install
```
2. Change `config.py`

All settings were stored in `config.example.py`.
After modifying it, the filename of `config.example.py` should be changed to `config.py`
```
TOKEN -> The bot's token
```

3. Run!
```bash
pipenv run python serve.py
```

## Dependencies
- httpx - async http request library
- aiogram - async telegram bot library
- websockets - async websockets client

## License
**This repo is licensed under the MIT license.**