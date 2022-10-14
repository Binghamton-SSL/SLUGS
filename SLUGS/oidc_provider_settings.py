def userinfo(claims, user):
    # Populate claims dict.
    claims['name'] = f'{user.first_name} {user.last_name}'
    claims['given_name'] = user.first_name
    claims['family_name'] = user.last_name
    claims['preferred_username'] = user.preferred_name
    claims['email'] = user.email
    claims['phone']['phone_number'] = user.phone_number
    
    return claims