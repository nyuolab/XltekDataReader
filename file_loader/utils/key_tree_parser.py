import re


class node:
    def __init__(self, key, data):
        self.key = key
        self.data = data

    def to_dict(self):
        if isinstance(self.data, list):
            d = dict()
            for item in self.data:
                d[item.key] = item.to_dict()
            return d
        else:
            # If not a list, just a value
            return self.data


class key_tree_parser:
    def __init__(self, string):
        self.parsed_tree = parse_key_tree(string)

    def to_dict(self):
        d = dict()
        for item in self.parsed_tree:
            d[item.key] = item.to_dict()
        return d


def parse_key_tree(t, start=0, end=-1, depth=0):
    lst_nodes = []
    found_key = False
    cursor = start
    stopping = len(t) if end == -1 else end

    while cursor < stopping:
        if t[cursor:cursor+3] == '(."' and t[cursor+3] not in [')', '(']:
            found_key = True
            cursor = cursor + 3

        if not found_key:
            cursor += 1

        else:
            # Find key
            next_quote = t.find('"', cursor)
            key = t[cursor:next_quote]

            # Open value
            if t[next_quote+3] != '(':
                next_paren_right = t.find(')', cursor)

                # Sometimes text has parenthesis.
                while t[next_paren_right+1] not in [',',')']:
                    next_paren_right = t.find(')', next_paren_right+1)

                val = t[next_quote+3:next_paren_right].encode("unicode-escape").decode()
                val = val.strip('"')  # String values have redundant double quotes

                # Might be a string of int
                if val.isdigit():  
                    val = int(val)
                # TODO: Will this cause a problem if we have an integer ID with leading 0's?

                # Might be a float
                try:
                    a = float(val)
                    val = a
                except:
                    pass

                # Add key, val to list
                lst_nodes.append(
                    node(key, val)
                )

            # Value is either pair or tree
            else:
                inside_text = False
                count = None
                cursor_inner = next_quote + 3
                while count != 0:
                    if count is None:
                        count = 0

                    if t[cursor_inner] == '"':
                        inside_text = not inside_text

                    if t[cursor_inner] == '(' and not inside_text:
                        count += 1
                    elif t[cursor_inner] == ')' and not inside_text:
                        count -= 1

                    cursor_inner += 1
                next_paren_right = cursor_inner

                res = parse_key_tree(
                            t=t,
                            start=next_quote+3,
                            end=cursor_inner+1,
                            depth=depth+1
                        )

                lst_nodes.append(
                    node(
                        key,
                        res
                    )
                )

            cursor = next_paren_right+1
            found_key = False
    
    return lst_nodes
