class CardValidator:
    @staticmethod
    def validate_set_codes(set_codes):
        if not set_codes:
            return False, "No set codes provided"
        
        for code in set_codes:
            if not code.strip():
                return False, "Empty set code found"
            if not code.isalnum():
                return False, "Set codes must be alphanumeric"
            if len(code) > 10:
                return False, "Set code too long"
                
        return True, set_codes

    @staticmethod
    def validate_owned_quantity(quantity):
        try:
            qty = int(quantity)
            if qty < 0:
                return False, "Quantity cannot be negative"
            if qty > 999:
                return False, "Quantity cannot exceed 999"
            return True, qty
        except ValueError:
            return False, "Please enter a valid number"

    @staticmethod
    def validate_card_data(card):
        required_fields = ["Name", "Set", "Number"]
        for field in required_fields:
            if not card.get(field):
                return False, f"Missing required field: {field}"
                
        return True, None