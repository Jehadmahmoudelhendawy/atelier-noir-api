import logging
from assistify.apps.orders.models import Order
from assistify.ml_models.orchestrator import ModelOrchestrator
from assistify.apps.users.models import Notification

logger = logging.getLogger(__name__)

_recommendation_model = None

def get_recommendation_model():
    global _recommendation_model
    if _recommendation_model is None:
        _recommendation_model = ModelOrchestrator()
    return _recommendation_model

def generate_recommendations_for_user(user):
    """
    Generates product recommendations based on the user's order history,
    and creates a notification for them.
    """
    try:
        orders = Order.objects.filter(user=user).prefetch_related('items')
        
        past_product_names = []
        for order in orders:
            for item in order.items.all():
                past_product_names.append(item.product_name)
        
        model = get_recommendation_model()
        
        query = ""
        if past_product_names:
            last_product_name = past_product_names[0]
            from assistify.apps.products.models import Product
            last_product = Product.objects.filter(name=last_product_name).first()
            
            if last_product and last_product.category:
                query = last_product.get_category_display()
                logger.info(f"Generating recommendations for {user.username} based on category: {query}")
            else:
                query = last_product_name.split()[0] if last_product_name else "الصحة"
                logger.info(f"Generating recommendations for {user.username} based on past purchase: {query}")
        else:
            query = "الصحة"
            logger.info(f"User {user.username} has no history. Generating general recommendations.")
            
        recommendations, method = model._get_recommendations_stable(user_id=user.id, intent="recommendation", query=query)
        
        if not recommendations:
            logger.info("No recommendations generated.")
            return False
            
        new_recommendations = []
        past_names_lower = [name.lower() for name in past_product_names]
        
        for rec in recommendations:
            if rec['name'].lower() not in past_names_lower:
                new_recommendations.append(rec)
                
        if not new_recommendations:

            new_recommendations = recommendations
            
        title = "✨ خصيصاً لك: توصيات بناءً على طلباتك السابقة" if past_product_names else "✨ منتجات قد تهمك"
        
        message_lines = [
            f"مرحباً {user.username}، لقد اخترنا لك هذه المنتجات التي قد تعجبك:\n"
        ]
        
        for idx, rec in enumerate(new_recommendations[:3]):
            message_lines.append(f"{idx+1}. {rec['emoji']} {rec['name']} - {rec['price']} {rec['currency']}")
            if 'reasoning' in rec and rec['reasoning']:
                message_lines.append(f"   {rec['reasoning']}")
                
        message = "\n".join(message_lines)
        
        Notification.objects.create(
            user=user,
            title=title,
            message=message
        )
        
        logger.info(f"Successfully created recommendation notification for {user.username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations for {user.username}: {e}")
        return False
