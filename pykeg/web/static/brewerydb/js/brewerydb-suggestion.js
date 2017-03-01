angular.module('BreweryDbTypeahead', ['ngAnimate', 'ngSanitize', 'ui.bootstrap']);
angular.module('BreweryDbTypeahead').controller('TypeaheadCtrl', function($scope, $http) {

    var _selectedBeer;

    $scope.selected = undefined;
    // Any function returning a promise object can be used to load values asynchronously
    $scope.getBeers = function(val) {
        return $http.get('/api/brewerydb', {
            params: {
                q: val,
            }
        }).then(function(response){
            return response.data.objects.map(function(item) {
                item.displayName = item.breweries[0].name + ' - ' + item.nameDisplay;
                return item
            });
        });
    };

    $scope.beerSelected = function(value) {
        if (value) {
            $scope.selectedBeer = value;

            if (value.constructor === {}.constructor) {
                brewery = $scope.selectedBeer.breweries[0]
                brewery_location = brewery.locations[0]
                angular.element('#id_name').val($scope.selectedBeer.nameDisplay)
                angular.element('#id_style').val($scope.selectedBeer.style.name)
                angular.element('#id_abv_percent').val($scope.selectedBeer.abv)
                angular.element('#id_original_gravity').val($scope.selectedBeer.style.ogMin)
                angular.element('#id_specific_gravity').val($scope.selectedBeer.style.fgMin)
                angular.element('#id_ibu').val($scope.selectedBeer.ibu)
                angular.element('#id_srm').val($scope.selectedBeer.style.srmMin)
                angular.element('#id_description').val($scope.selectedBeer.description)
                angular.element('#id_brewery_db_image_url').val($scope.getImage($scope.selectedBeer))
                angular.element('#id_brewer_name').val(brewery.name)
                angular.element('#id_brewer_state').val(brewery_location.region)
                angular.element('#id_brewer_city').val(brewery_location.locality)
                angular.element('#id_brewer_url').val(brewery.website)
                angular.element('#id_brewer_description').val(brewery.description)
            }
        }

        return $scope.selectedBeer;
    };

    $scope.getImage = function(value) {
        if (value.labels) {
            labels = value.labels
            if (typeof labels.medium != 'undefined') {
                return labels.medium
            } else if(typeof labels.small != 'undefined') {
                return labels.small
            } else if(typeof labels.icon != 'undefined') {
                return labels.icon
            }
        }

        return ''
    }

    $scope.modelOptions = {
        debounce: {
            default: 500,
            blur: 250
        },
        getterSetter: true
    };
});