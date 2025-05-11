# LinkedIn Profile Search FastAPI Backend

This FastAPI backend exposes an API to search for LinkedIn profiles using the [linkedin-api](https://github.com/nsandman/linkedin-api) library.

## Setup

1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2. Set your LinkedIn credentials as environment variables:
    ```bash
    export LINKEDIN_USERNAME=your_email@example.com
    export LINKEDIN_PASSWORD=your_password
    ```
   Or create a `.env` file with:
    ```env
    LINKEDIN_USERNAME=your_email@example.com
    LINKEDIN_PASSWORD=your_password
    ```

3. Run the server:
    ```bash
    uvicorn main:app --reload
    ```

## API Usage

### Search People

`GET /search?query=your+search+terms`

**Example:**
```
GET /search?query=recruiters+zeta
```

**Response:**
```json
[
  {
    "name": "John Doe",
    "profile_url": "https://www.linkedin.com/in/johndoe",
    "current_org": "Recruiter at Zeta"
  },
  ...
]
```

## Notes
- This project uses an unofficial LinkedIn API and may be subject to LinkedIn's rate limits or account restrictions. Use at your own risk.
- For more details, see the [linkedin-api documentation](https://github.com/nsandman/linkedin-api/blob/master/DOCS.md#search_people).