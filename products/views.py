import json

from cores.utils      import author
from django.http      import JsonResponse
from django.views     import View
from django.http      import JsonResponse
from django.db.models import Q

from products.models import Category, Product, Ingredient, SkinType, ProductFeelings, Review

class RecommendedView(View):
    def get(self, request, product_id):
        try:
            category_id   = Product.objects.get(id = product_id).category
            products      = Product.objects.filter(category = category_id).exclude(id=product_id)
            
            recommend_list = [{
                'name'      : product.name,
                'image'     : [image.url for image in product.productimage_set.all()],
                'skintype'  : [types.skin_type.name for types in product.productskintype_set.all()]
                } for product in products]

            return JsonResponse({'result' : recommend_list }, status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KEY_ERROR'} , status = 401)
        except Product.DoesNotExist:
            return JsonResponse({'message' : 'PRODUCT_DOES_EXIST'} , status = 401)

class ProductListView(View):
    def get(self, request):
        category_id   = request.GET.get('category_id', None)
        offset        = int(request.GET.get('offset', 0))
        limit         = int(request.GET.get('limit', 100))
        ingredient_id = request.GET.getlist('ingredient_id', None)
        skintype_id   = request.GET.getlist('skintype_id', None)
        scent         = request.GET.get('scent', None)
        feeling_id    = request.GET.get('feeling_id', None)
        search        = request.GET.get('search', None)
        
        q = Q()

        if search:
            q &= Q(name__icontains=search)

        if category_id:
            q &= Q(category__id=category_id)

        if scent:
            q &= Q(howtouse__scent__contains=scent)
        
        if ingredient_id:
            q &= Q(productingredient__ingredient__id__in=ingredient_id)
        
        if skintype_id:
            q &= Q(productskintype__skin_type__id__in=skintype_id)
        
        if feeling_id:
            q &= Q(productfeelings__feeling__id__in=feeling_id)

        products = Product.objects.filter(q)[offset:offset+limit]

        result = [{
            'id'         : product.id,
            'badge'      : product.badge,
            'productName': product.name,
            'size'       : product.size,
            'price'      : product.price,
            'feeling'    : [feeling.feeling.name for feeling in product.productfeelings_set.all()],
            'ingredient' : [item.ingredient.name for item in product.productingredient_set.all()],
            'skin_type'  : [productskintype.skin_type.name for productskintype in product.productskintype_set.all()],
            'url'        : [img.url for img in product.productimage_set.all()],
            'howtouse'   : product.howtouse,
            'category'   : {
                'categoryId'            : product.category.id,
                'categoryName'          : product.category.category_name,
                'categoryDescription'   : product.category.main_description,
                'categorySubDescription': product.category.sub_description
            }
        } for product in products]
        return JsonResponse({'result':result}, status=200)

class ProductDetailView(View):
    def get(self, request, product_id):
        try: 
            product = Product.objects.get(id = product_id)
            main_ingredients = Ingredient.objects.filter(productingredient__product_id = product.id, productingredient__major = True)
            skin_type        = SkinType.objects.filter(productskintype__product_id = product_id)
            feelings         = ProductFeelings.objects.filter(product = product_id)
            product_detail = {
                'id'                : product.id,
                'name'              : product.name,
                'price'             : product.price,
                'size'              : product.size,
                'category'          : product.category.category_name,
                'description'       : product.description,
                'feeling'           : [feeling.feeling.name for feeling in feelings],
                'product_imges'     : [image.url for image in product.productimage_set.all()],
                'main_ingredients'  : [ingredient.name for ingredient in main_ingredients],
                'ingredients'       : [ingredient.name for ingredient in Ingredient.objects.filter(productingredient__product = product_id)],
                'skin_type'         : [type.name for type in skin_type]
            }
            howtouse = product.howtouse
              
            return JsonResponse({'result' : [ product_detail , howtouse ] } , status = 200)
        except KeyError:
            return JsonResponse({'message' : 'KEY_ERROR'} , status = 404)
        except Product.DoesNotExist:
            return JsonResponse({'message' : 'PRODUCT_NAME_ERROR'} , status = 404)


class CategoryListView(View):
    def get(self, request):
        offset = int(request.GET.get('offset', 0))
        limit  = int(request.GET.get('limit', 100))

        categories = Category.objects.all()[offset:offset+limit]
        
        result = [{
            'categoryId'            : category.id,
            'categoryName'          : category.category_name,
            'categoryDescription'   : category.main_description,
            'categorySubDescription': category.sub_description
        } for category in categories]

        return JsonResponse({'result':result}, status=200)


class CategoryDetailView(View):
    def get(self, request, category_id):        
        category = Category.objects.get(id=category_id)
        
        result = {
            'categoryId'            : category.id,
            'categoryName'          : category.category_name,
            'categoryDescription'   : category.main_description,
            'categorySubDescription': category.sub_description
        }

        return JsonResponse({'result':result}, status=200)
    
class ProductReviewView(View):
    def get(self, request):
        try:
            data = json.loads(request.body)
            reviews =Review.objects.filter(product_id = data['product_id'])
            
            if not reviews.exists():
                return JsonResponse({'message' : 'PRODUCT_REVIEW_DOES_NOT_EXIST'} , status = 404)
            
            result = [{
                    'review_id' : review.id,
                    'user'      : review.user.email,
                    'content'   : review.content
                } for review in reviews]
            return JsonResponse({'message' : result} , status =200)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'} , status = 400)
        except Product.DoesNotExist:
            return JsonResponse({'message' : 'PRODUCT_DOES_NOT_EXIST'} , status = 400)
    
    @author
    def post(self, request):
        try:
            data = json.loads(request.body)
            content     = data['content']
            user        = request.user
            product     = Product.objects.get(id = data['product_id'])
            
            Review.objects.create(  
                user    = user,
                product = product, 
                content = content
            )
             
            return JsonResponse({'message' : 'SUCCESS'} , status = 201) 
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'} , status = 400)
        except Product.DoesNotExist:
            return JsonResponse({'message' : 'PRODUCT_DOES_NOT_EXIST'} , status = 404)
    
    @author
    def delete(self, request, review_id):
        review      = Review.objects.filter(user = request.user , id = review_id)
            
        if not review.exists():
            return JsonResponse({'message' : 'UNAUTHORIZED_REQUEST'} , status = 404)
        
        review.delete()
            
        return JsonResponse({'message' : 'SUCCESS'} , status = 200)

   
