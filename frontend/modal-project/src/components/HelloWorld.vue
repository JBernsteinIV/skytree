<script>
  export default {
    name: 'HelloWorld',
    props: ['address', 'port', 'route' ],
    data() {
      return {services: []}
    },
    methods: {
    getServices: function get_services(address, port, route) 
    {
      /* 
      *  fetch takes two parameters:
      *  1) The URL to query
      *  2) An object specifying the method and optionally: Content-Type, data, etc. //This object is optional for GET methods.
      */
      const response = fetch(`http://${this.address}:${this.port}/${this.route}`, {method: 'GET'})
                      // On success, parse the data. In this case rendering / handling as JSON.
                      .then(resp => resp.json())
                      // Now we need to store the parsed data into an object to access the data.
                      .then(data => this.services = data)
                      // On error, indicate the failure reason. Return a message indicating this isn't working.
                      .catch(err => {
                        console.log(`ERROR! ${err}`)
                        return [
                          {
                            "status" : 400,
                            "message": err
                          }
                        ]
                      })
      return response
    }
    }
  }
</script>
<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
<template>
  <button @click="getServices">Get Services</button>
  <table id="serviceTable">
    <tbody>
      <th>
        <td>Name</td>
        <td>State</td>
        <td>Description</td>
      </th>
      <tr v-for="service in services">
        <div v-if="service.state == 'running'">
          <td>{{ service.name }}</td>
          <td>{{ service.state }}</td>
          <td>{{ service.description }}</td>
        </div>
      </tr>
    </tbody>
  </table>
</template>