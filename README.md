Alfred workflow to modify beancount file with account/payee auto-complete. Thanks to [beancount](http://furius.ca/beancount/), [Alfred-Workflow](http://www.deanishe.net/alfred-workflow/) and [iconmonstr](http://iconmonstr.com/). Please remember to modify the corresponding regex in `beancount.json` to match your entry format.

### Append a new entry to existing beancount file

> bean-add FROM_ACCOUNT TO_ACCOUNT '[PAYEE]' AMOUNT '[TAGS]' '[COMMENT]'

### Rebuild account and payee caches

> bean-cache [PATH_TO_BEANCOUNT_FILE]

### Clear an transaction by adding #clear tag

> bean-clear [FROM_ACCOUNT]