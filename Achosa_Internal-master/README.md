# achosa
### Two Apps:  
- Home Claims
- Home Warranty

https://restyn.monday.com/boards/123063667/

V13 5/20/2021

# Release 03/06/23

This is a release branch! It contains a few issues that have made it to UAT.
## Included changes:
- Short-list:
    - AO-1035
    - AO-1049
    - AO-1051
    - ~~AO-1005~~
    - AO-1038

- AO-1035
    - Changes to sub end date calculations, now for Buyer subs the end date is calculated when the related invoice is paid

- AO-1049
    - Add scripts directory with two scripts:
        - createLogDir.sh
        - detect-rebuild.sh

- AO-1051
    - Modify email template logic to utilize new field, paid_email_template_id, to grab the correct template to send when an invoice is paid
    - #### This also includes config changes:
        - Scheduled action to fix products using old template (running on product.product model):

        ```
        targets = model.search([("paid_email_template_id", "=", env.ref("achosa.hw_paid").id)])
        for rec in targets:
            rec.write({"paid_email_template_id": env.ref("sale_subscription.mail_template_subscription_invoice")})
        ```
        - Also must change configuration settings for sales:

        ## Settings -> Sales -> Invoicing -> Automatic Invoice -> Invoice Email Template

        - Set to Invoice: Payment Confirmation 

- ~~AO-1005~~
    - ~~Change logic for promo code checking, fixing root cause for DRG failure~~

    - #### ~~This also includes config changes:~~
        - ~~For promo code DRG, make sure the product domain is set to:~~
        
        ~~[['name', 'ilike', 'CONSERVE PLUS']]~~

- AO-1038 
    - Minor change to http routes, already present in Master!
