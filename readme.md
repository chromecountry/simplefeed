# SimpleFeed #

## Preamble ##

This document makes the following assumptions:

  - developers have a working knowledge of:
  - Instagram API
  - Email systems (SMTP)
  
  - developers have a thorough knowledge of:
  - Python
  - Command line interfaces

## Introduction ##

SimpleFeed is a tool that eliminates endless Instagram scrolling while keeping you informed. It:

1. Automatically monitors your Instagram timeline for topics you care about
2. Filters posts using your custom keywords
3. Delivers a curated email digest containing:
   - Relevant posts from your community
   - Associated images
   - User information
   - Matching keywords

The goal is to help users:
- Stay informed without the social media time sink
- Focus on specific topics or community interests
- Receive organized, relevant content directly in their inbox
- Break free from algorithmic feeds and endless scrolling

## Configuration ##

### Environment Variables ###

No environment variables required.

### Credentials ###

### credentials.py ###

Copy credentials_template.py to credentials.py and configure:

Instagram credentials:
- USERNAME
- PASSWORD

Gmail credentials:
- EMAIL
- PASSWORD

Note: For Gmail, use App Password if 2FA is enabled.

### Installation ###

Ensure Python 3.7 or greater is available. Install requirements:

```
$ pip install -r requirements.txt
```

## Workflow ##

### Running SimpleFeed ###

Basic usage:

```
$ python simple_feed.py -i search_terms.txt -w 24
```

Arguments:
- `-i, --input`: File containing search your terms (one per line)
- `-w, --window`: Look-back window in hours (default: 24)

### Sample Input File ###
```
event
tour
showing
show

```

### Output ###

Sends email digest containing:
- Matching posts from specified time window
- Associated images
- User information
- Matching search terms

Email subject format: `SimpleFeed Newsletter YYYY-MM-DD`
