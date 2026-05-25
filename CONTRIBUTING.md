# Contributing

1. Fork the repo at https://github.com/neardaniel-pls/near-investing
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Push and open a pull request

## Code Style

- Follow PEP 8
- Use type hints for function signatures
- Use `src/` modules for logic, `pages/` for Streamlit UI
- Keep pages thin — delegate computation to `src/` modules
- Use `st.session_state` for shared data across pages

## Testing

- Test your changes by running `streamlit run app.py`
- Verify all pages load correctly with sample data
- Test both Beginner and Advanced UI modes

## Commit Messages

Use conventional commits: `feat`, `fix`, `docs`, `refactor`, `chore`
