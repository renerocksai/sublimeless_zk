def split_regions(regions):
    num_regions_in = len(regions)
    start_index = 0
    new_regions = []
    did_replace = False
    while start_index < num_regions_in:
        region = regions[start_index]
        if start_index == num_regions_in - 1:
            new_regions.append(region)
            break
        subregion = regions[start_index + 1]
        if subregion[0] >= region[0] and subregion[1] <= region[1]:
            new_subs = []
            # merge and append
            did_replace = True
            if subregion[0] == region[0]:
                new_subs.append(subregion)
            else:
                pre = subregion[0] - region[0]
                new_subs.append((region[0], region[0] + pre, region[2][:pre], region[3]))
                new_subs.append(subregion)
            if subregion[1] < region[1]:
                post = region[1] - subregion[1]
                new_subs.append((subregion[1], region[1], region[2][-post:], region[3]))
            new_regions.extend(new_subs)
            start_index += 2  ## skip this one as it has been merged
        else:
            # no need to look further
            new_regions.append(region)
            start_index += 1
            # continue with the next outer region
    # append the last region
    return did_replace, new_regions


if __name__ == '__main__':
    regions = [
        (0, 10, '1234567890', 'heading'),
        (2, 5, '345', 'bold')
    ]
    print(regions)
    print(split_regions(regions))

    regions = [
        (0, 10, '1234567890', 'heading'),
        (7, 10, '890', 'bold')
    ]
    print(regions)
    print(split_regions(regions))

    regions = [
        (0, 10, '1234567890', 'heading'),
        (0, 3, '123', 'bold')
    ]
    print(regions)
    print(split_regions(regions))

