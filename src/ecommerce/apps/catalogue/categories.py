from oscar.core.loading import get_model

Category = get_model('catalogue', 'category')


def create_from_sequence(bits):
    """
    Create categories from an iterable
    """
    if len(bits) == 1:
        # Get or create root node
        name = bits[0]
        try:
            # Category names should be unique at the depth=1
            root = Category.objects.get(depth=1, name=name)
        except Category.DoesNotExist:
            root = Category.add_root(name=name)
        except Category.MultipleObjectsReturned as e:
            raise ValueError(
                f"There are more than one categories with name {name} at depth=1"
            ) from e
        return [root]
    else:
        parents = create_from_sequence(bits[:-1])
        parent, name = parents[-1], bits[-1]
        try:
            child = parent.get_children().get(name=name)
        except Category.DoesNotExist:
            child = parent.add_child(name=name)
        except Category.MultipleObjectsReturned as e:
            raise ValueError(
                f"There are more than one categories with name {name} which are children of {parent}"
            ) from e
        parents.append(child)
        return parents


def create_from_breadcrumbs(breadcrumb_str, separator='>'):
    """
    Create categories from a breadcrumb string
    """
    category_names = [x.strip() for x in breadcrumb_str.split(separator)]
    categories = create_from_sequence(category_names)
    return categories[-1]
