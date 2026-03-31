def is_palindrome(s: str) -> bool:
    """Check if a string is a palindrome (case-insensitive, ignores non-alphanumeric)."""
    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]


# Test cases
assert is_palindrome("A man, a plan, a canal: Panama") == True
assert is_palindrome("race a car") == False
assert is_palindrome(" ") == True
assert is_palindrome("") == True
assert is_palindrome("Was it a car or a cat I saw?") == True
assert is_palindrome("No lemon, no melon") == True
assert is_palindrome("hello") == False
assert is_palindrome("Madam") == True
assert is_palindrome("12321") == True
assert is_palindrome("123abccba321") == True
assert is_palindrome("123abccba32x") == False

print("All tests passed!")
