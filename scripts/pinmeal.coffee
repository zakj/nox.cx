class Spot extends Backbone.Model
  urlRoot: '/pinmeal'
  defaults:
    goodFor: []
    visits: []

  today: ->
    d = new Date
    "#{d.getFullYear()}-#{d.getMonth() + 1}-#{d.getDate()}"

  visitedToday: ->
    visits = @get('visits')
    return false unless visits
    _(visits).contains(@today())

  visit: ->
    # We only allow one visit per day as a simple guard against multi-clicks.
    return if @visitedToday()
    # Cloning the existing value to ensure a change event fires (since
    # otherwise we'd just be mutating the existing value).
    visits = _.clone(@get('visits')) or []
    visits.push(@today())
    @set('visits', visits)


class SpotCollection extends Backbone.Collection
  model: Spot
  url: '/pinmeal'

  # Order by least-recently visited.
  comparator: (spot) ->
    _.min(spot.get('visits'))

  goodFor: (what) ->
    @filter (spot) -> _(spot.get('goodFor')).contains(what)


## Views  ####################################################################

# Display a single spot.
class SpotView extends Backbone.View
  tagName: 'li'
  template: Handlebars.templates.spot

  initialize: ->
    @model.on('change', @render)
    @model.on('error', @showError)

  render: =>
    context = @model.toJSON()
    context.visitedToday
    @$el.html(@template(@model.toJSON()))
    return this

  events:
    'dblclick': 'edit'
    'click .visit': 'visit'

  edit: ->
    editView = new SpotEditView(model: @model)
    @$el.html(editView.render().el)

  visit: ->
    @model.visit()
    @model.save()

  showError: (response) =>
    console.log('error', response)  # XXX
    @$el.css('background-color', '#fdd')
    @model.fetch()


class SpotEditView extends Backbone.View
  tagName: 'form'
  template: Handlebars.templates.spotEdit

  render: ->
    context = @model.toJSON()
    context.goodForOptions = ['lunch', 'dinner', 'drinks']  # XXX DRY
    @$el.html(@template(context))
    _.delay => @$('input').first().focus() unless @model.id
    return this

  events:
    'change input': 'change'
    'submit': 'submit'
    'click [type=reset]': 'cancel'

  change: (event) ->
    input = $(event.target)
    name = input.attr('name')
    value = input.val()
    if input.attr('type') is 'checkbox'
      value = _(@$("[name=#{name}]:checked")).map (el) -> $(el).val()
    @model.set(input.attr('name'), value, silent: true)

  submit: (event) ->
    event.preventDefault()
    @remove()
    @model.save({}, error: @handleError)
    # XXX if no changed properties, we never redisplay the main view

  cancel: (event) ->
    event.preventDefault()
    @remove()
    @model.fetch()

  handleError: (spot, response) ->
    spot.trigger('error', response)


class SpotsView extends Backbone.View

  render: (spots) ->
    frag = document.createDocumentFragment()
    _(spots).each (spot) ->
      frag.appendChild(new SpotView(model: spot).render().el)
    @$el.html(frag)
    return this

  add: (spot) ->
    view = new SpotView(model: spot).render()
    view.edit()
    @$el.append(view.el)


## Main application  #########################################################

class Pinmeal extends Backbone.View

  initialize: ->
    @spots = new SpotCollection
    @spotsView = new SpotsView(el: $('#spots'))
    @spots.on('reset', => @spotsView.render(@spots.models))
    @spots.on('add', (spot) => @spotsView.add(spot))

  events:
    'click #new': 'newSpot'
    'click #lunch': 'showLunch'
    'click #dinner': 'showDinner'
    'click #drinks': 'showDrinks'

  newSpot: ->
    @spots.add({})

  showLunch: ->
    @spotsView.render(@spots.goodFor('lunch'))

  showDinner: ->
    @spotsView.render(@spots.goodFor('dinner'))

  showDrinks: ->
    @spotsView.render(@spots.goodFor('drinks'))




## Handlebars  ###############################################################

Handlebars.registerHelper 'ifContains', (haystack, needle, options) ->
  if _(haystack).contains(needle)
    options.fn(this)
  else
    options.inverse(this)

Handlebars.registerHelper 'pluralize', (number, single, plural, options) ->
  # plural is an optional argument; if missing, just append an "s" to single.
  if arguments.length is 3
    plural = undefined
  if number is 1
    single
  else if plural?
    plural
  else
    single + 's'


## Exports  ##################################################################

this.app = new Pinmeal(el: $('body'))




## XXX TEMP

places = new google.maps.places.PlacesService(document.createElement('div'))
mississippiSkidmore = new google.maps.LatLng(45.554614,-122.675518)
milesInMeters = (miles) -> miles * 1609.3

request =
  location: mississippiSkidmore
  radius: milesInMeters(5)
  types: ['restaurant', 'bar', 'food', 'establishment']
places.nearbySearch request, (results, status) ->
  console.log status
  console.log results
  ###
  status is google.maps.places.PlacesServiceStatus.OK
  each result:
    icon: "http://maps.gstatic.com/mapfiles/place_api/icons/lodging-71.png"
    id: "694c3d4659d9224d0d1a1b57ced42e70eb41160d"
    name: "Portland Marriott Downtown Waterfront"
    rating: 3.9
    reference: "..."
    types: Array[2]
    vicinity: "1401 Southwest Naito Parkway, Portland"
  ###

testref = "CoQBcQAAABX795xeCfj8jJ4MYYw4yIvyLeaoAyPIO8FliOAIrVFwZxij4PCwwFq6ndGC5EBIQiTX0h42dn2HAT8NjaM_aAkDWW_zMHo58D4iSNcJz8AdcVUolx8NtxRKrlS2FPSL46nbUhPEcm7I58SviX0Vuhx05EtlkJaGx1vQDQzWR0xJEhDWIY4i7u-cDdwcDjiig2HDGhRdm32b4h8eD_1Phpf6-8S7MFPb3Q"
places.getDetails reference: testref, (details, status) ->
  console.log status
  #console.log details
  d = details
  console.log(
    d.name
    d.icon
    d.formatted_phone_number
    d.rating
    d.types
    d.website
    d.url
  )
  ###
    address_components: Array[6]
    formatted_address: "111 Southwest 5th Avenue, Portland, OR, United States"
    formatted_phone_number: "(503) 450-0030"
    geometry: Object
    html_attributions: Array[0]
    icon: "http://maps.gstatic.com/mapfiles/place_api/icons/bar-71.png"
    id: "59daf0d6bb4bb0270c5adc0bf817d4545c8270e2"
    international_phone_number: "+1 503-450-0030"
    name: "Portland City Grill"
    rating: 4
    reference:
    reviews: Array[5]
    types: Array[4]
    tz: "GMT-0700"
    url: "https://plus.google.com/107421001095610256273/about?hl=en-US"
    utc_offset: -420
    vicinity: "111 Southwest 5th Avenue, Portland"
    website: "http://www.portlandcitygrill.com/"
  ###

llrToBounds = (latLng, radius) ->
  new google.maps.Circle(center: latLng, radius: radius).getBounds()

input = document.getElementById('autocomplete')
options =
  bounds: llrToBounds(mississippiSkidmore, milesInMeters(5))
  types: ['establishment']
this.ac = new google.maps.places.Autocomplete(input, options)

google.maps.event.addListener ac, 'place_changed', ->
  console.log('foo')
  console.log(@getPlace())


#acService = new google.maps.places.AutocompleteService
#cb = (predictions, status) ->
#  console.log status, predictions
#acService.getQueryPredictions(input: 'pizza near', cb)
