# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in DocuAI, please email **parveenbirthaliya@gmail.com** instead of using the issue tracker.

Please include:
- Type of vulnerability
- Location in code
- Potential impact
- Steps to reproduce (if applicable)

We will acknowledge receipt within 48 hours and provide a detailed update within 1 week.

## Supported Versions

| Version | Supported          |
|---------|-------------------|
| 1.0.x   | ✅ Supported      |
| < 1.0   | ❌ Not supported  |

## Security Best Practices

When using DocuAI:

1. **API Keys**: Never commit `.env` files or keys to version control
2. **Model URLs**: Be careful with model/API endpoints in production
3. **Data Sanitization**: Sanitize user inputs before passing to LLM
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Access Control**: Restrict access to retrieval/generation endpoints
6. **Dependencies**: Keep dependencies updated (`pip install --upgrade -r requirements.txt`)

## Vulnerability Disclosure Timeline

1. **Day 0**: Vulnerability reported
2. **Day 2**: Acknowledgment sent
3. **Day 7**: Initial assessment and mitigation plan
4. **Day 14**: Fix released or timeline provided
5. **Day 30**: Full disclosure if timeline exceeded

## Security Updates

Follow us for security updates:
- Watch releases on GitHub
- Subscribe to security advisories
- Check `requirements.txt` for pinned versions

---

Thank you for helping keep DocuAI secure!
