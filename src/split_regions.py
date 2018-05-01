class CascadingStyleRegions:
    def __init__(self, text):
        self.len = len(text)
        self.text = text
        self.char_styles = ['default' for i in range(self.len)]
        self.regions = None
    
    def apply_regions(self, regions):
        if not regions:
            self.regions = []
            return[]

        # sort regions by length, biggest first, and apply them
        for region in reversed(sorted(regions, key=lambda x: x[1] - x[0])):
            self.char_styles[region[0]:region[1]] = [region[3]] * (region[1] - region[0])
        
        # now collapse them
        new_regions = []
        current_style = self.char_styles[0]
        current_start = 0
        for index, style in enumerate(self.char_styles):
            if style != current_style:
                # style change
                new_regions.append((current_start, index, self.text[current_start:index], current_style))
                current_start = index
                current_style = style
        # append last region
        if current_start != self.len:
            new_regions.append((current_start, self.len, self.text[current_start:self.len], current_style))
        self.regions = new_regions
        return self.regions


if __name__ == '__main__':
    regions = [
        (0, 10, '1234567890', 'heading'),
        (0, 3, '123', 'bold'),
        (0, 5, '12345', 'italic')
    ]
    a = CascadingStyleRegions('1234567890 hello world')
    regions = a.apply_regions(regions)
    print('character styles:', a.char_styles)
    print('\n'.join([str(region) for region in regions]))

