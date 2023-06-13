app = Vue.createApp({
    data() {
        return {
            toggleBooks: true,
            btnMsg: "Hide",
            title: "The Final Empire",
            author: "Brandon Sanderson",
            age: 45
        }
    },
    methods: {
        changeTitle() {
            this.title = 'Vue For Dummies'
        },
        showBooks() {
            this.toggleBooks != true ? this.btnMsg = "Hide" : this.btnMsg = "Show"
            this.toggleBooks = !this.toggleBooks
        }
    }
})

app.mount('#app')