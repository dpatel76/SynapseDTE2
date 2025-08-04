    async def authenticate_user(self, email: str, password: str = "AdminUser123!") -> str:
        """Authenticate user and return JWT token"""
        if email in self.auth_tokens:
            return self.auth_tokens[email]
            
        # Use different password for test users
        if email.endswith("@synapse.com"):
            password = "TestUser123!"
            
        auth_data = {"email": email, "password": password} 