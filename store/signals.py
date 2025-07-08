# store/signals.py
import cloudinary
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from .models import Product, ProductImage


@receiver(pre_delete, sender=Product)
def delete_product_images_from_cloudinary(sender, instance, **kwargs):
    """
    Signal handler che elimina tutte le immagini associate al prodotto
    da Cloudinary prima che il prodotto venga eliminato dal database.
    """
    # Ottieni tutte le immagini associate al prodotto
    product_images = instance.images.all()

    for product_image in product_images:
        if product_image.image:
            try:
                # Estrai il public_id dall'URL dell'immagine Cloudinary
                public_id = product_image.image.public_id

                # Elimina l'immagine da Cloudinary
                cloudinary.uploader.destroy(public_id)

                print(f"Immagine eliminata da Cloudinary: {public_id}")

            except Exception as e:
                print(f"Errore nell'eliminazione dell'immagine da Cloudinary: {str(e)}")


@receiver(post_delete, sender=ProductImage)
def delete_single_image_from_cloudinary(sender, instance, **kwargs):
    """
    Signal handler che elimina una singola immagine da Cloudinary
    quando viene eliminata dal database.
    """
    if instance.image:
        try:
            # Estrai il public_id dall'URL dell'immagine Cloudinary
            public_id = instance.image.public_id

            # Elimina l'immagine da Cloudinary
            cloudinary.uploader.destroy(public_id)

            print(f"Immagine eliminata da Cloudinary: {public_id}")

        except Exception as e:
            print(f"Errore nell'eliminazione dell'immagine da Cloudinary: {str(e)}")