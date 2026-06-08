
def initialize_memory():

    return []


def add_message(memory, role, content):

    memory.append({
        "role": role,
        "content": content
    })

    return memory