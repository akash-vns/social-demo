def unfriend_user(current_user, other_user):
    current_user.friends.remove(other_user)
    other_user.friends.remove(current_user)
