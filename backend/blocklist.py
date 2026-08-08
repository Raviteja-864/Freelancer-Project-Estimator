"""
Simple in-memory JWT blocklist for handling logout.
NOTE: In production, replace this with a persistent store (Redis is recommended)
since an in-memory set will reset on server restart and won't work across
multiple worker processes.
"""

BLOCKLIST = set()
